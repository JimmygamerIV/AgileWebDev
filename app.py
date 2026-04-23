from flask import Flask, render_template, redirect, session, request, jsonify
from database import init_db, Session
from models import Event, User, Friend, FriendRequest
from auth import auth_bp
from datetime import date, timedelta, datetime
from pathlib import Path
import json
from icalendar import Calendar
from map_ics_uid_locations import resolve_location, build_alias_index, build_room_index
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlparse


app = Flask(__name__)
app.secret_key = 'somesecretkey'

init_db()
app.register_blueprint(auth_bp)


# -------------------------
# File paths / data loading
# -------------------------

BASE_DIR = Path(__file__).parent
TIMETABLES_DIR = BASE_DIR / "timetables"
TIMETABLES_DIR.mkdir(parents=True, exist_ok=True)

with (BASE_DIR / "buildings.json").open(encoding="utf-8") as f:
    BUILDINGS = json.load(f)

with (BASE_DIR / "pois.json").open(encoding="utf-8") as f:
    POIS = json.load(f)

ALIAS_INDEX = build_alias_index(BUILDINGS)
ROOM_INDEX = build_room_index(POIS)


# -------------------------
# ICS Import Logic
# -------------------------

def importICS(ics_content, user_id):
    cal = Calendar.from_ical(ics_content)

    db = Session()
    try:
        db.query(Event).filter(Event.user_id == user_id).delete()

        preview_events = []

        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            event_name = str(component.get("SUMMARY") or "Untitled")
            start = component.get("DTSTART").dt
            end = component.get("DTEND").dt

            day = start.strftime("%A")
            event_date = start.strftime("%Y-%m-%d")
            start_time = start.strftime("%H:%M")
            end_time = end.strftime("%H:%M")

            raw_location = str(component.get("LOCATION") or "")
            location = resolve_location(raw_location, POIS, BUILDINGS, ALIAS_INDEX, ROOM_INDEX)

            new_event = Event(
                user_id=user_id,
                event_name=event_name,
                location=location,
                day=day,
                date=event_date,
                start_time=start_time,
                end_time=end_time
            )

            db.add(new_event)

            preview_events.append({
                "event_name": event_name,
                "date": event_date,
                "start_time": start_time,
                "end_time": end_time
            })

        db.commit()
        return preview_events

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()


def user_timetable_path(user_id):
    return TIMETABLES_DIR / f"user_{user_id}.ics"


# -------------------------
# Routes
# -------------------------

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/signin')

    db = Session()
    try:
        user = db.query(User).filter(User.user_id == session['user_id']).first()
        all_events = db.query(Event).filter(Event.user_id == session['user_id']).order_by(Event.date, Event.start_time).all()

        events = []

        today = date.today()
        tomorrow = today + timedelta(days=1)
        time_now = datetime.now().strftime("%H:%M")

        for e in all_events:
            if not e.date:
                continue

            event_date = date.fromisoformat(e.date)

            if event_date == today and e.start_time >= time_now:
                events.append(e)

            elif event_date == tomorrow:
                events.append(e)

        if not events:
            for e in all_events:
                if not e.date:
                    continue

                event_date = date.fromisoformat(e.date)

                if event_date > tomorrow:
                    events.append(e)

                if len(events) == 2:
                    break

    finally:
        db.close()

    return render_template(
        "index.html",
        events=events,
        username=user.username,
        show_full_nav=True
    )


# -------------------------
# Add Event
# -------------------------

@app.route('/add-event', methods=['GET', 'POST'])
def add_event():
    if 'user_id' not in session:
        return redirect('/signin')

    db = Session()
    user = db.query(User).filter(User.user_id == session['user_id']).first()
    db.close()

    error = None
    success = None
    preview_events = []

    if request.method == 'POST':
        uploaded_file = request.files.get("ics_file")
        ics_url = request.form.get("ics_url", "").strip()

        has_file = uploaded_file and uploaded_file.filename != ""
        has_url = bool(ics_url)

        if not has_file and not has_url:
            error = "Please upload a file or provide a URL."

        elif has_file:
            if not uploaded_file.filename.endswith(".ics"):
                error = "Only .ics files are supported."
            else:
                try:
                    ics_content = uploaded_file.read()
                    user_timetable_path(session['user_id']).write_bytes(ics_content)
                    preview_events = importICS(ics_content, session['user_id'])
                    success = "Timetable imported successfully."
                except Exception:
                    error = "Could not parse this ICS file."

        else:
            parsed = urlparse(ics_url)

            if parsed.scheme not in {"http", "https"}:
                error = "Please provide a valid URL."
            else:
                try:
                    with urlopen(ics_url, timeout=20) as response:
                        ics_content = response.read()

                    user_timetable_path(session['user_id']).write_bytes(ics_content)
                    preview_events = importICS(ics_content, session['user_id'])
                    success = "Timetable imported successfully."

                except URLError:
                    error = "Could not download from that URL."

                except Exception:
                    error = "Could not parse the ICS content."

    return render_template(
        "add_event.html",
        error=error,
        success=success,
        preview_events=preview_events,
        has_saved_timetable=user_timetable_path(session['user_id']).exists(),
        username=user.nickname or user.username,
        show_full_nav=True
    )


# -------------------------
# Restore Timetable (FIXED)
# -------------------------

@app.route('/timetable/restore', methods=['POST'])
def restore_timetable():
    if 'user_id' not in session:
        return redirect('/signin')

    saved_path = user_timetable_path(session['user_id'])

    if not saved_path.exists():
        return render_template(
            "add_event.html",
            error="No saved timetable found.",
            success=None,
            preview_events=[],
            has_saved_timetable=False,
            show_full_nav=True
        ), 404

    try:
        ics_content = saved_path.read_bytes()
        preview_events = importICS(ics_content, session['user_id'])

        return render_template(
            "add_event.html",
            error=None,
            success="Timetable restored successfully.",
            preview_events=preview_events,
            has_saved_timetable=True,
            show_full_nav=True
        )

    except Exception:
        return render_template(
            "add_event.html",
            error="Could not restore the saved timetable.",
            success=None,
            preview_events=[],
            has_saved_timetable=True,
            show_full_nav=True
        ), 500


# -------------------------
# Friends Page
# -------------------------

@app.route('/friends')
def friends():
    if 'user_id' not in session:
        return redirect('/signin')

    db = Session()
    try:
        user_id = session['user_id']

        friend_ids = [f.friend_id for f in db.query(Friend).filter(Friend.user_id == user_id).all()]
        friends_list = db.query(User).filter(User.user_id.in_(friend_ids)).all()

        r_rows = db.query(FriendRequest).filter(
            FriendRequest.receiver_id == user_id,
            FriendRequest.status == 'pending'
        ).all()

        sender_ids = [r.sender_id for r in r_rows]
        senders = db.query(User).filter(User.user_id.in_(sender_ids)).all()

        requests = []
        for r in r_rows:
            for s in senders:
                if s.user_id == r.sender_id:
                    requests.append({
                        "request_id": r.request_id,
                        "user_id": s.user_id,
                        "username": s.username
                    })

        return render_template(
            "friends.html",
            friends=friends_list,
            requests=requests,
            show_full_nav=True
        )

    finally:
        db.close()


# -------------------------
# Run
# -------------------------

if __name__ == "__main__":
    app.run(debug=True)