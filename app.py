from flask import Flask, g, render_template, redirect, session, request, jsonify
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


BASE_DIR = Path(__file__).parent
TIMETABLES_DIR = BASE_DIR / "timetables"
TIMETABLES_DIR.mkdir(parents=True, exist_ok=True)

with (BASE_DIR / "buildings.json").open(encoding="utf-8") as f:
    BUILDINGS = json.load(f)
with (BASE_DIR / "pois.json").open(encoding="utf-8") as f:
    POIS = json.load(f)

ALIAS_INDEX = build_alias_index(BUILDINGS)
ROOM_INDEX = build_room_index(POIS)


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


def is_event_currently_running(event, now=None):
    if not event.date or not event.start_time or not event.end_time:
        return False

    try:
        start_dt = datetime.strptime(f"{event.date} {event.start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{event.date} {event.end_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return False

    # Handle events that cross midnight.
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    if now is None:
        now = datetime.now()

    return start_dt <= now < end_dt



def get_event_time_window(event):
    if not event.date or not event.start_time or not event.end_time:
        return None

    try:
        start_dt = datetime.strptime(f"{event.date} {event.start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{event.date} {event.end_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None

    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    return start_dt, end_dt


def events_overlap(first_event, second_event):
    first_window = get_event_time_window(first_event)
    second_window = get_event_time_window(second_event)
    if first_window is None or second_window is None:
        return False

    first_start, first_end = first_window
    second_start, second_end = second_window
    return first_start < second_end and second_start < first_end


def select_current_or_next_event(events, now=None):
    if now is None:
        now = datetime.now()

    current_events = []
    upcoming_events = []

    for event in events:
        window = get_event_time_window(event)
        if window is None:
            continue

        start_dt, end_dt = window
        if start_dt <= now < end_dt:
            current_events.append((start_dt, event))
        elif start_dt > now:
            upcoming_events.append((start_dt, event))

    if current_events:
        return min(current_events, key=lambda item: item[0])[1]
    if upcoming_events:
        return min(upcoming_events, key=lambda item: item[0])[1]
    return None


def get_primary_poi_id(location_value):
    if not location_value:
        return None

    for token in str(location_value).split("|"):
        poi_id = token.strip()
        if poi_id in POIS:
            return poi_id

    return None


def get_friend_ids(db, user_id):
    rows = db.query(Friend).filter(
        (Friend.user_id == user_id) | (Friend.friend_id == user_id)
    ).all()

    friend_ids = set()
    for row in rows:
        if row.user_id == user_id:
            friend_ids.add(row.friend_id)
        if row.friend_id == user_id:
            friend_ids.add(row.user_id)

    return friend_ids


@app.route('/')
def index():
    if g.current_user is None:
        session.pop('user_id', None)
        return redirect('/signin')
    
    db = Session()
    try:
        user = db.query(User).filter(User.user_id == session['user_id']).first()
        all_events = db.query(Event).filter(Event.user_id == session['user_id']).order_by(Event.date, Event.start_time).all()
        events = []

        today = date.today()
        tomorrow = today + timedelta(days=1)
        time_now = datetime.now().strftime("%H:%M")

        # Add today's and tommorow's classes to the array
        for e in all_events:
            if not e.date:
                continue
            event_date = date.fromisoformat(e.date)

            if event_date == today and e.end_time and e.end_time > time_now:
                events.append(e)

            elif event_date == tomorrow:
                events.append(e)
        
        # If there are no upcomming classes for the two days then add next furutre upcoming
        if not events:
            for e in all_events:
                if not e.date:
                    continue

                event_date = date.fromisoformat(e.date)
                if event_date > tomorrow:
                    events.append(e)

                # Only add the next 2 upcoming events
                if len(events) == 2:
                    break
                
    finally:
        db.close()

    return render_template("index.html", events=events, username=g.current_user["nickname"] or g.current_user["username"])


@app.route('/add-event', methods=['GET', 'POST'])
def add_event():
    if g.current_user is None:
        session.pop('user_id', None)
        return redirect('/signin')


    error = None
    success = None
    preview_events = []
    
    if request.method == 'POST':
        uploaded_file = request.files.get("ics_file")
        ics_url = request.form.get("ics_url", "").strip()
        
        has_file = uploaded_file is not None and uploaded_file.filename != ""
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
    
    return render_template("add_event.html",
    error=error,
    success=success,
    preview_events=preview_events,
    has_saved_timetable=user_timetable_path(session['user_id']).exists(),
    username=g.current_user["nickname"] or g.current_user["username"]
    )


@app.route('/timetable/restore', methods=['POST'])
def restore_timetable():
    if 'user_id' not in session:
        return redirect('/signin')
    
    saved_path = user_timetable_path(session['user_id'])
    if not saved_path.exists():
        return render_template("add_event.html",
            error="No saved timetable found.",
            success=None,
            preview_events=[],
            has_saved_timetable=False
        ), 404
    
    try:
        ics_content = saved_path.read_bytes()
        preview_events = importICS(ics_content, session['user_id'])
        return render_template("add_event.html",
            error=None,
            success="Timetable restored successfully.",
            preview_events=preview_events,
            has_saved_timetable=True
        )
    except Exception:
        return render_template("add_event.html",
            error="Could not restore the saved timetable.",
            success=None,
            preview_events=[],
            has_saved_timetable=True
        ), 500

@app.route('/api/events/me', methods=['GET'])
def my_events():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    db = Session()
    try:
        events = db.query(Event).filter(
            Event.user_id == session['user_id']
        ).order_by(Event.date, Event.start_time).all()
        
        result = []
        for e in events:
            if e.date and date.fromisoformat(e.date) < date.today():
                continue
            result.append({
                "event_id": e.event_id,
                "event_name": e.event_name or "Untitled",
                "location": e.location or "",
                "day": e.day or "",
                "day_display": e.day or "",
                "date":e.date or "",
                "start_time": e.start_time or "",
                "end_time": e.end_time or "",
            })
        
        return jsonify({"user_id": session['user_id'], "events": result})
    
    finally:
        db.close()


@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    db = Session()
    try:
        event = db.get(Event, event_id)
        if event is None:
            return jsonify({"error": "Event not found"}), 404
        if event.user_id != session['user_id']:
            return jsonify({"error": "Forbidden"}), 403
        if is_event_currently_running(event):
            return jsonify({"error": "This event is currently running and can only be deleted after it ends."}), 409
        
        db.delete(event)
        db.commit()
        return jsonify({"success": True, "event_id": event_id, "deleted": True})
    
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    
    finally:
        db.close()


@app.route('/api/map/current-class', methods=['GET'])
def current_class_map_data():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user_id = session['user_id']

    db = Session()
    try:
        my_events = db.query(Event).filter(Event.user_id == user_id).all()
        target_event = select_current_or_next_event(my_events)

        if target_event is None:
            return jsonify({"class": None})

        poi_id = get_primary_poi_id(target_event.location or "")
        poi = POIS.get(poi_id) if poi_id else None

        building_id = None
        if poi_id and "." in poi_id:
            building_id = poi_id.split(".", 1)[0]
        if poi and poi.get("parent_building"):
            building_id = poi.get("parent_building")

        building = BUILDINGS.get(building_id, {}) if building_id else {}
        building_name = (
            building.get("name")
            or (poi.get("building_name") if poi else None)
            or "Unknown building"
        )

        latitude = None
        longitude = None
        if poi:
            latitude = poi.get("latitude")
            longitude = poi.get("longitude")
        if latitude is None or longitude is None:
            latitude = building.get("latitude")
            longitude = building.get("longitude")

        attendees = set()
        if target_event.date and poi_id:
            same_day_events = db.query(Event).filter(
                Event.date == target_event.date,
                Event.user_id != user_id,
            ).all()

            for event in same_day_events:
                if get_primary_poi_id(event.location or "") != poi_id:
                    continue
                if not events_overlap(target_event, event):
                    continue
                attendees.add(event.user_id)

        friend_ids = get_friend_ids(db, user_id)
        friend_nicknames = []
        if attendees:
            attendee_users = db.query(User).filter(User.user_id.in_(attendees)).all()
            for attendee in attendee_users:
                if attendee.user_id in friend_ids:
                    friend_nicknames.append(attendee.nickname or attendee.username)

        friend_nicknames.sort(key=str.lower)

        return jsonify({
            "class": {
                "event_name": target_event.event_name or "Untitled",
                "date": target_event.date or "",
                "start_time": target_event.start_time or "",
                "end_time": target_event.end_time or "",
                "time_display": f"{target_event.start_time or ''} - {target_event.end_time or ''}".strip(" -"),
                "building_name": building_name,
                "floor": (poi.get("floor") if poi else None),
                "location_display": poi_id or (target_event.location or "Unknown location"),
                "latitude": latitude,
                "longitude": longitude,
                "other_attendees_count": len(attendees),
                "friend_nicknames": friend_nicknames,
            }
        })

    finally:
        db.close()


@app.route('/friends')
def friends():
    if 'user_id' not in session:
        return redirect('/signin')

    db = Session()
    try:
        user_id = session['user_id']

        friend_ids = []
        # Get all friends for the user
        f_rows = db.query(Friend).filter(Friend.user_id == user_id).all()

        for i in f_rows:
            friend_ids.append(i.friend_id)

        friends_list = db.query(User).filter(User.user_id.in_(friend_ids)).all()

        # Friend Requests
        r_rows = db.query(FriendRequest).filter(
            FriendRequest.receiver_id == user_id,
            FriendRequest.status == 'pending'
        ).all()

        sender_ids = []
        for i in r_rows:
            sender_ids.append(i.sender_id)
        
        senders = db.query(User).filter(User.user_id.in_(sender_ids)).all()

        requests = []
        for r in r_rows:
            for s in senders:
                # Check if user found
                if s.user_id == r.sender_id:
                    requests.append({
                        "request_id": r.request_id,
                        "user_id": s.user_id,
                        "username": s.username
                    })
                    break
        
        return render_template(
            "friends.html",
            friends=friends_list,
            requests=requests
        )
                
    finally:
        db.close()

if __name__ == "__main__":
    app.run(debug=True)