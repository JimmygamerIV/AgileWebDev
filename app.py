import os
import json
from datetime import date, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen
from flask import Flask, g, jsonify, redirect, render_template, request, url_for
from icalendar import Calendar
from werkzeug.utils import secure_filename

from database import Session as DBSession
from database import init_db
import models
from auth import auth_bp
from map_ics_uid_locations import build_alias_index, build_room_index, resolve_location

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-change-this-secret")

BASE_DIR = Path(__file__).parent
TIMETABLES_DIR = BASE_DIR / "timetables"
TIMETABLES_DIR.mkdir(parents=True, exist_ok=True)

with (BASE_DIR / "buildings.json").open(encoding="utf-8") as buildings_file:
    BUILDINGS = json.load(buildings_file)
with (BASE_DIR / "pois.json").open(encoding="utf-8") as pois_file:
    POIS = json.load(pois_file)

ALIAS_INDEX = build_alias_index(BUILDINGS)
ROOM_INDEX = build_room_index(POIS)

init_db()

app.register_blueprint(auth_bp)


def _format_time(value):
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    return ""


def _extract_iso_day(value):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return ""


def _ordinal(day_number):
    if 10 <= day_number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day_number % 10, "th")
    return f"{day_number}{suffix}"


def _format_day_display(day_value):
    if not day_value:
        return ""

    try:
        parsed_date = date.fromisoformat(day_value)
        return f"{parsed_date.strftime('%A')} ({parsed_date.strftime('%B')} {_ordinal(parsed_date.day)})"
    except ValueError:
        # Backward compatibility for older rows that stored weekday names only.
        return day_value


def _is_past_day(day_value):
    if not day_value:
        return False

    try:
        parsed_date = date.fromisoformat(day_value)
    except ValueError:
        # Keep legacy rows that don't use ISO dates.
        return False

    # Keep current-day classes even if their time has already passed.
    return parsed_date < date.today()


def _load_existing_events_for_user(user_id):
    db = DBSession()
    try:
        existing = (
            db.query(models.Event)
            .filter(models.Event.user_id == user_id)
            .order_by(models.Event.day, models.Event.start_time)
            .all()
        )
        return [
            {
                "event_id": event.event_id,
                "event_name": event.event_name or "Untitled Event",
                "day": event.day or "",
                "day_display": _format_day_display(event.day or ""),
                "start_time": event.start_time or "",
                "end_time": event.end_time or "",
                "location": event.location or "",
            }
            for event in existing
            if not _is_past_day(event.day or "")
        ]
    finally:
        db.close()


def _import_ics_for_user(ics_content, user_id):
    calendar = Calendar.from_ical(ics_content)
    preview_events = []

    db = DBSession()
    try:
        db.query(models.Event).filter(models.Event.user_id == user_id).delete()

        for component in calendar.walk():
            if component.name != "VEVENT":
                continue

            event_name = str(component.get("SUMMARY") or "Untitled Event")
            start_dt = component.get("DTSTART").dt if component.get("DTSTART") else None
            end_dt = component.get("DTEND").dt if component.get("DTEND") else None

            start_time = _format_time(start_dt)
            end_time = _format_time(end_dt)
            day = _extract_iso_day(start_dt)

            if _is_past_day(day):
                continue

            raw_location = str(component.get("LOCATION") or "").strip()
            mapped_location = resolve_location(raw_location, POIS, BUILDINGS, ALIAS_INDEX, ROOM_INDEX)
            location = mapped_location or raw_location

            new_event = models.Event(
                user_id=user_id,
                event_name=event_name,
                location=location,
                day=day,
                start_time=start_time,
                end_time=end_time,
            )
            db.add(new_event)
            db.flush()

            preview_events.append(
                {
                    "event_id": new_event.event_id,
                    "event_name": event_name,
                    "day": day,
                    "day_display": _format_day_display(day),
                    "start_time": start_time,
                    "end_time": end_time,
                    "location": location,
                }
            )

        db.commit()
        return preview_events
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _user_timetable_path(user_id):
    return TIMETABLES_DIR / f"user_{user_id}.ics"

@app.route('/')
def index():
    if g.current_user is None:
        return redirect(url_for("auth.signin"))
    return render_template("index.html")


@app.route('/timetable/restore', methods=["POST"])
def restore_timetable():
    if g.current_user is None:
        return redirect(url_for("auth.signin"))

    user_ics_path = _user_timetable_path(g.current_user["user_id"])
    if not user_ics_path.exists():
        return render_template(
            "AddEvent.html",
            error="No saved timetable found for this user.",
            success=None,
            preview_events=[],
            has_saved_timetable=False,
        ), 404

    try:
        ics_content = user_ics_path.read_bytes()
        preview_events = _import_ics_for_user(ics_content, g.current_user["user_id"])
        return render_template(
            "AddEvent.html",
            error=None,
            success="Saved ICS restored and timetable replaced successfully.",
            preview_events=preview_events,
            has_saved_timetable=True,
        )
    except Exception:
        return render_template(
            "AddEvent.html",
            error="Could not restore the saved ICS file.",
            success=None,
            preview_events=[],
            has_saved_timetable=True,
        ), 500


@app.route('/api/events/me', methods=["GET"])
def my_events():
    if g.current_user is None:
        return jsonify({"error": "Not authenticated"}), 401

    db = DBSession()
    try:
        events = (
            db.query(models.Event)
            .filter(models.Event.user_id == g.current_user["user_id"])
            .order_by(models.Event.day, models.Event.start_time)
            .all()
        )
        filtered_events = [event for event in events if not _is_past_day(event.day or "")]

        return jsonify(
            {
                "user_id": g.current_user["user_id"],
                "events": [
                    {
                        "event_id": event.event_id,
                        "event_name": event.event_name or "Untitled Event",
                        "location": event.location or "",
                        "day": event.day or "",
                        "day_display": _format_day_display(event.day or ""),
                        "start_time": event.start_time or "",
                        "end_time": event.end_time or "",
                    }
                    for event in filtered_events
                ],
            }
        )
    finally:
        db.close()


@app.route('/api/events/<int:event_id>', methods=["DELETE"])
def delete_event(event_id):
    if g.current_user is None:
        return jsonify({"error": "Not authenticated"}), 401

    db = DBSession()
    try:
        event = db.get(models.Event, event_id)
        if event is None:
            print(f"[DELETE] Event ID {event_id} not found in database")
            return jsonify({"error": "Event not found"}), 404

        if event.user_id != g.current_user["user_id"]:
            print(f"[DELETE] Event ID {event_id} does not belong to user {g.current_user['user_id']}")
            return jsonify({"error": "Forbidden"}), 403

        print(f"[DELETE] Deleting event {event_id}: {event.event_name} for user {g.current_user['user_id']}")
        db.delete(event)
        db.commit()
        print(f"[DELETE] Successfully committed deletion of event {event_id}")

        return jsonify({"success": True, "event_id": event_id, "deleted": True})
    except Exception as e:
        print(f"[DELETE] ERROR deleting event {event_id}: {str(e)}")
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@app.route('/add-event', methods=["GET", "POST"])
def add_event():
    if g.current_user is None:
        return redirect(url_for("auth.signin"))

    error = None
    success = None
    preview_events = []

    if request.method == "POST":
        uploaded_file = request.files.get("ics_file")
        ics_url = request.form.get("ics_url", "").strip()

        has_file = uploaded_file is not None and uploaded_file.filename != ""
        has_url = bool(ics_url)

        if not has_file and not has_url:
            error = "Please upload an ICS file or provide an ICS URL."
        elif has_file:
            safe_name = secure_filename(uploaded_file.filename)
            if not safe_name.lower().endswith(".ics"):
                error = "Only .ics files are supported."
            else:
                user_ics_path = _user_timetable_path(g.current_user["user_id"])
                ics_content = uploaded_file.read()
                user_ics_path.write_bytes(ics_content)

                try:
                    preview_events = _import_ics_for_user(ics_content, g.current_user["user_id"])
                    success = "ICS uploaded. Previous timetable replaced successfully."
                except Exception:
                    error = "Could not parse this ICS file. Please upload a valid timetable export."
        else:
            parsed_url = urlparse(ics_url)
            if parsed_url.scheme not in {"http", "https"}:
                error = "Please provide a valid http(s) ICS URL."
            else:
                try:
                    with urlopen(ics_url, timeout=20) as response:
                        ics_content = response.read()
                except URLError:
                    error = "Could not download the ICS URL. Please verify the link and try again."
                else:
                    user_ics_path = _user_timetable_path(g.current_user["user_id"])
                    user_ics_path.write_bytes(ics_content)
                    try:
                        preview_events = _import_ics_for_user(ics_content, g.current_user["user_id"])
                        success = "ICS link imported. Previous timetable replaced successfully."
                    except Exception:
                        error = "Could not parse the ICS content from that URL."

    return render_template(
        "AddEvent.html",
        error=error,
        success=success,
        preview_events=preview_events,
        has_saved_timetable=_user_timetable_path(g.current_user["user_id"]).exists(),
    )

if __name__ == "__main__":
    app.run(debug=True)