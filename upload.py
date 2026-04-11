import urllib.request
from icalendar import Calendar
from sqlalchemy import create_engine
from map_ics_uid_locations import resolve_location, build_alias_index, build_room_index
import json
from models import Event
from database import Session

url = "https://apps.cas.uwa.edu.au/even/rest/calendar/ical/bfa21375-c6be-4507-b82a-076c42c94543"

with urllib.request.urlopen(url) as response:
    cal = Calendar.from_ical(response.read())

engine = create_engine("sqlite:///unimap.db")

session = Session()

with open("buildings.json") as f:
    buildings = json.load(f)

with open("pois.json") as f:
    pois = json.load(f)

alias_index = build_alias_index(buildings)
room_index = build_room_index(pois)

user_id = 1

# Delete existing entry if exists
session.query(Event).filter(Event.user_id == user_id).delete()

for component in cal.walk():
    if component.name == "VEVENT":
        event_name = component.get("SUMMARY")

        # Get the datetime
        start = component.get("DTSTART").dt
        end = component.get("DTEND").dt

        # Extract date and time separately
        day = start.strftime("%A")
        start_time = start.strftime("%H:%M")
        end_time = end.strftime("%H:%M")

        raw_location = str(component.get("LOCATION") or "")
        # Filter raw location
        location = resolve_location(raw_location, pois, buildings, alias_index, room_index)

        new_event = Event(
            user_id = user_id,
            event_name = event_name,
            location = location,
            day = day,
            start_time = start_time,
            end_time = end_time
        )

        session.add(new_event)

session.commit()
session.close()