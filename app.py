from flask import Flask, render_template, redirect, session, request
from database import init_db, Session
from models import Event, User
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


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/signin')
    
    db = Session()
    try:
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

            if event_date == today and e.start_time >= time_now:
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

    return render_template("index.html", events=events)


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
        has_saved_timetable=False
    )


if __name__ == "__main__":
    app.run(debug=True)