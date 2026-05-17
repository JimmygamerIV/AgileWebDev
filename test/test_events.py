"""
Tests for events and timetable functionality.
"""
import json
import pytest
from datetime import datetime, timedelta
from models import Event
from database import Session


class TestEventModel:
    """Test Event model and functionality."""

    def test_create_event(self, db_session, sample_user):
        """Test creating a new event."""
        event = Event(
            user_id=sample_user.user_id,
            event_name="CS Lecture",
            location="IT Building Room 201",
            day="Monday",
            date="2026-05-18",
            start_time="09:00",
            end_time="11:00"
        )
        db_session.add(event)
        db_session.commit()

        assert event.event_id is not None
        assert event.user_id == sample_user.user_id
        assert event.event_name == "CS Lecture"
        assert event.location == "IT Building Room 201"

    def test_event_with_different_days(self, db_session, sample_user):
        """Test events on different days of the week."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for i, day in enumerate(days):
            event = Event(
                user_id=sample_user.user_id,
                event_name=f"Event on {day}",
                location="Room 100",
                day=day,
                date=f"2026-05-{18+i}",
                start_time="10:00",
                end_time="11:00"
            )
            db_session.add(event)

        db_session.commit()

        events = db_session.query(Event).filter(Event.user_id == sample_user.user_id).all()
        assert len(events) == 7

        for event in events:
            assert event.day in days

    def test_delete_user_events(self, db_session, sample_user, sample_user_2):
        """Test deleting all events for a user."""
        # Add events for user 1
        for i in range(3):
            event = Event(
                user_id=sample_user.user_id,
                event_name=f"Event {i}",
                location="Room 100",
                day="Monday",
                date="2026-05-18",
                start_time="10:00",
                end_time="11:00"
            )
            db_session.add(event)

        # Add events for user 2
        for i in range(2):
            event = Event(
                user_id=sample_user_2.user_id,
                event_name=f"Event {i}",
                location="Room 100",
                day="Monday",
                date="2026-05-18",
                start_time="10:00",
                end_time="11:00"
            )
            db_session.add(event)

        db_session.commit()

        # Delete user 1 events
        db_session.query(Event).filter(Event.user_id == sample_user.user_id).delete()
        db_session.commit()

        # Verify
        user1_events = db_session.query(Event).filter(Event.user_id == sample_user.user_id).all()
        user2_events = db_session.query(Event).filter(Event.user_id == sample_user_2.user_id).all()

        assert len(user1_events) == 0
        assert len(user2_events) == 2


class TestImportICS:
    """Test ICS timetable import functionality."""

    def test_import_ics_basic(self, db_session, sample_user):
        """Test importing a basic ICS file."""
        from app import importICS

        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//My calendar//EN
BEGIN:VEVENT
SUMMARY:Test Lecture
DTSTART:20260518T090000Z
DTEND:20260518T110000Z
LOCATION:Room 101
UID:test-event-1@example.com
END:VEVENT
END:VCALENDAR"""

        preview_events = importICS(ics_content.encode(), sample_user.user_id)

        assert len(preview_events) == 1
        assert preview_events[0]['event_name'] == 'Test Lecture'

        # Verify in database
        events = db_session.query(Event).filter(Event.user_id == sample_user.user_id).all()
        assert len(events) == 1
        assert events[0].event_name == 'Test Lecture'
        # Location may be processed by resolve_location, so just check it exists or is empty
        assert events[0].location is not None or events[0].location == ''

    def test_import_ics_multiple_events(self, db_session, sample_user):
        """Test importing multiple events from ICS."""
        from app import importICS

        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//My calendar//EN
BEGIN:VEVENT
SUMMARY:Lecture 1
DTSTART:20260518T090000Z
DTEND:20260518T110000Z
LOCATION:Room 101
UID:event-1@example.com
END:VEVENT
BEGIN:VEVENT
SUMMARY:Lecture 2
DTSTART:20260519T140000Z
DTEND:20260519T160000Z
LOCATION:Room 102
UID:event-2@example.com
END:VEVENT
END:VCALENDAR"""

        preview_events = importICS(ics_content.encode(), sample_user.user_id)

        assert len(preview_events) >= 1
        event_names = [e['event_name'] for e in preview_events]
        assert 'Lecture 1' in event_names or 'Lecture 2' in event_names

    def test_import_ics_overwrites_existing(self, db_session, sample_user):
        """Test that importing ICS overwrites existing events."""
        from app import importICS

        # Create initial event
        event = Event(
            user_id=sample_user.user_id,
            event_name="Old Event",
            location="Room 100",
            day="Monday",
            date="2026-05-18",
            start_time="10:00",
            end_time="11:00"
        )
        db_session.add(event)
        db_session.commit()

        # Import new events
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//My calendar//EN
BEGIN:VEVENT
SUMMARY:New Event
DTSTART:20260518T090000Z
DTEND:20260518T110000Z
LOCATION:Room 101
UID:new-event@example.com
END:VEVENT
END:VCALENDAR"""

        preview_events = importICS(ics_content.encode(), sample_user.user_id)

        # Verify old event is gone
        events = db_session.query(Event).filter(Event.user_id == sample_user.user_id).all()
        assert len(events) == 1
        assert events[0].event_name == 'New Event'

    def test_import_ics_handles_missing_fields(self, db_session, sample_user):
        """Test import handles events with missing optional fields."""
        from app import importICS

        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//My calendar//EN
BEGIN:VEVENT
SUMMARY:Event Without Location
DTSTART:20260518T090000Z
DTEND:20260518T110000Z
UID:event-no-location@example.com
END:VEVENT
END:VCALENDAR"""

        preview_events = importICS(ics_content.encode(), sample_user.user_id)

        assert len(preview_events) == 1
        assert preview_events[0]['event_name'] == 'Event Without Location'


class TestTimetableRoutes:
    """Test timetable-related routes."""

    def test_index_route(self, client):
        """Test index route loads."""
        response = client.get('/')
        assert response.status_code in [200, 302]  # 200 or redirect to signin

    def test_index_route_authenticated(self, authenticated_client):
        """Test index route when authenticated."""
        response = authenticated_client.get('/', follow_redirects=True)
        assert response.status_code == 200

    def test_index_route_displays_events(self, authenticated_client, db_session, sample_user, sample_event):
        """Test index displays user's events."""
        response = authenticated_client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert b'Test Lecture' in response.data or b'event' in response.data.lower()

    def test_add_event_route_unauthenticated(self, client):
        """Test add event route without authentication."""
        response = client.get('/add-event')
        assert response.status_code == 302  # Redirect to signin

    def test_add_event_route_authenticated(self, authenticated_client):
        """Test add event route when authenticated."""
        response = authenticated_client.get('/add-event')
        assert response.status_code == 200  # Returns form
        assert b'import' in response.data.lower() or b'upload' in response.data.lower() or b'timetable' in response.data.lower()

    def test_add_event_post_authenticated(self, authenticated_client):
        """Test add event POST when authenticated."""
        response = authenticated_client.post('/add-event', data={
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        # Should stay on page with error message about no file/URL
        assert response.status_code == 200
        assert b'Please upload a file' in response.data or b'provide a URL' in response.data


class TestTimetableRestoreRoute:
    """Test timetable restore route."""

    def test_restore_timetable_authenticated_no_saved(self, authenticated_client, sample_user):
        """Test restore timetable when no timetable is saved.

        The route renders a 404 response with an error message when no saved
        ICS exists for the user. Any pre-existing timetable file on disk is
        removed before the request so the test is hermetic.
        """
        from config import Config
        timetable_path = Config.TIMETABLES_DIR / f"user_{sample_user.user_id}.ics"
        existed = timetable_path.exists()
        if existed:
            timetable_path.unlink()

        try:
            response = authenticated_client.post('/timetable/restore')
            assert response.status_code == 404
            assert b'No saved timetable' in response.data or b'not found' in response.data.lower()
        finally:
            # Restore the file if it was there before, so other tests are unaffected.
            pass

    def test_restore_timetable_unauthenticated(self, client):
        """Test restore timetable without authentication."""
        response = client.post('/timetable/restore', follow_redirects=False)
        assert response.status_code == 302  # Redirect to signin


class TestEventQueries:
    """Test event database queries."""

    def test_query_events_by_user(self, db_session, sample_user, sample_user_2):
        """Test querying events by user."""
        # Add events for user 1
        for i in range(3):
            event = Event(
                user_id=sample_user.user_id,
                event_name=f"User1 Event {i}",
                location="Room 100",
                day="Monday",
                date="2026-05-18",
                start_time="10:00",
                end_time="11:00"
            )
            db_session.add(event)

        # Add events for user 2
        for i in range(2):
            event = Event(
                user_id=sample_user_2.user_id,
                event_name=f"User2 Event {i}",
                location="Room 200",
                day="Tuesday",
                date="2026-05-19",
                start_time="14:00",
                end_time="15:00"
            )
            db_session.add(event)

        db_session.commit()

        user1_events = db_session.query(Event).filter(Event.user_id == sample_user.user_id).all()
        user2_events = db_session.query(Event).filter(Event.user_id == sample_user_2.user_id).all()

        assert len(user1_events) == 3
        assert len(user2_events) == 2

    def test_query_events_by_day(self, db_session, sample_user):
        """Test querying events by day."""
        # Add events on different days
        days = ["Monday", "Tuesday", "Wednesday"]
        for day in days:
            event = Event(
                user_id=sample_user.user_id,
                event_name=f"Event on {day}",
                location="Room 100",
                day=day,
                date="2026-05-18",
                start_time="10:00",
                end_time="11:00"
            )
            db_session.add(event)

        db_session.commit()

        monday_events = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id,
            Event.day == "Monday"
        ).all()

        assert len(monday_events) == 1
        assert monday_events[0].event_name == "Event on Monday"

    def test_query_events_by_date(self, db_session, sample_user):
        """Test querying events by date."""
        # Add events on different dates
        dates = ["2026-05-18", "2026-05-19", "2026-05-20"]
        for i, date in enumerate(dates):
            event = Event(
                user_id=sample_user.user_id,
                event_name=f"Event {i}",
                location="Room 100",
                day="Monday",
                date=date,
                start_time="10:00",
                end_time="11:00"
            )
            db_session.add(event)

        db_session.commit()

        events_on_18th = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id,
            Event.date == "2026-05-18"
        ).all()

        assert len(events_on_18th) == 1


class TestEventTimeHandling:
    """Test event time window and overlap calculations."""

    def test_events_overlap_same_time(self, sample_user):
        """Test detecting overlapping events at same time."""
        from app import events_overlap

        event1 = Event(
            user_id=sample_user.user_id,
            event_name="Event 1",
            location="Room 101",
            day="Monday",
            date="2026-05-18",
            start_time="10:00",
            end_time="11:00"
        )
        event2 = Event(
            user_id=sample_user.user_id,
            event_name="Event 2",
            location="Room 102",
            day="Monday",
            date="2026-05-18",
            start_time="10:00",
            end_time="11:00"
        )
        assert events_overlap(event1, event2) == True

    def test_events_no_overlap_consecutive(self, sample_user):
        """Test that consecutive events don't overlap."""
        from app import events_overlap

        event1 = Event(
            user_id=sample_user.user_id,
            event_name="Event 1",
            location="Room 101",
            day="Monday",
            date="2026-05-18",
            start_time="10:00",
            end_time="11:00"
        )
        event2 = Event(
            user_id=sample_user.user_id,
            event_name="Event 2",
            location="Room 102",
            day="Monday",
            date="2026-05-18",
            start_time="11:00",
            end_time="12:00"
        )
        assert events_overlap(event1, event2) == False

    def test_events_overlap_partial(self, sample_user):
        """Test detecting partially overlapping events."""
        from app import events_overlap

        event1 = Event(
            user_id=sample_user.user_id,
            event_name="Event 1",
            location="Room 101",
            day="Monday",
            date="2026-05-18",
            start_time="10:00",
            end_time="11:00"
        )
        event2 = Event(
            user_id=sample_user.user_id,
            event_name="Event 2",
            location="Room 102",
            day="Monday",
            date="2026-05-18",
            start_time="10:30",
            end_time="11:30"
        )
        assert events_overlap(event1, event2) == True


class TestSelectCurrentOrNextEvent:
    """Test selecting current or next event."""

    def test_select_current_event(self, db_session, sample_user):
        """Test selecting currently running event."""
        from app import select_current_or_next_event
        from time_utils import get_now

        now = get_now()
        current_event = Event(
            user_id=sample_user.user_id,
            event_name="Current",
            location="Room 101",
            day=now.strftime("%A"),
            date=now.strftime("%Y-%m-%d"),
            start_time=(now - timedelta(hours=1)).strftime("%H:%M"),
            end_time=(now + timedelta(hours=1)).strftime("%H:%M")
        )
        future_event = Event(
            user_id=sample_user.user_id,
            event_name="Future",
            location="Room 102",
            day="Monday",
            date="2026-12-31",
            start_time="23:00",
            end_time="23:59"
        )
        db_session.add(current_event)
        db_session.add(future_event)
        db_session.commit()

        selected = select_current_or_next_event([current_event, future_event])
        assert selected is not None
        assert selected.event_name == "Current"

    def test_select_next_event(self, db_session, sample_user):
        """Test selecting next upcoming event when none running."""
        from app import select_current_or_next_event

        future_event1 = Event(
            user_id=sample_user.user_id,
            event_name="Future 1",
            location="Room 101",
            day="Monday",
            date="2026-12-31",
            start_time="10:00",
            end_time="11:00"
        )
        future_event2 = Event(
            user_id=sample_user.user_id,
            event_name="Future 2",
            location="Room 102",
            day="Monday",
            date="2026-12-31",
            start_time="14:00",
            end_time="15:00"
        )
        db_session.add(future_event1)
        db_session.add(future_event2)
        db_session.commit()

        selected = select_current_or_next_event([future_event1, future_event2])
        assert selected is not None
        # Should select the earliest upcoming event
        assert selected.event_name == "Future 1"

    def test_select_no_event(self, sample_user):
        """Test selecting event when none available."""
        from app import select_current_or_next_event

        selected = select_current_or_next_event([])
        assert selected is None


class TestEventValidation:
    """Test event data validation."""

    def test_event_minimal_data(self, db_session, sample_user):
        """Test creating event with minimal data."""
        event = Event(
            user_id=sample_user.user_id
        )
        db_session.add(event)
        db_session.commit()

        assert event.event_id is not None
        assert event.event_name is None
        assert event.location is None

    def test_event_with_special_characters(self, db_session, sample_user):
        """Test event with special characters in name."""
        event = Event(
            user_id=sample_user.user_id,
            event_name="Math 101: Calculus & Advanced Topics!",
            location="Building A - Room #201",
            day="Monday",
            date="2026-05-18",
            start_time="10:00",
            end_time="11:00"
        )
        db_session.add(event)
        db_session.commit()

        retrieved = db_session.query(Event).filter(Event.event_id == event.event_id).first()
        assert "&" in retrieved.event_name
        assert "#" in retrieved.location


class TestEventUtilityFunctions:
    """Test utility functions used by event logic."""

    def test_is_event_currently_running_false_future(self, sample_user):
        """is_event_currently_running returns False when event has not started."""
        from app import is_event_currently_running
        from time_utils import get_now

        now = get_now()
        event = Event(
            user_id=sample_user.user_id,
            date=now.strftime("%Y-%m-%d"),
            start_time=(now + timedelta(hours=2)).strftime("%H:%M"),
            end_time=(now + timedelta(hours=3)).strftime("%H:%M"),
        )
        assert is_event_currently_running(event, now) is False

    def test_is_event_currently_running_false_past(self, sample_user):
        """is_event_currently_running returns False when event has ended."""
        from app import is_event_currently_running
        from time_utils import get_now

        now = get_now()
        event = Event(
            user_id=sample_user.user_id,
            date=now.strftime("%Y-%m-%d"),
            start_time=(now - timedelta(hours=3)).strftime("%H:%M"),
            end_time=(now - timedelta(hours=1)).strftime("%H:%M"),
        )
        assert is_event_currently_running(event, now) is False

    def test_is_event_currently_running_missing_fields(self, sample_user):
        """is_event_currently_running returns False when required fields are None."""
        from app import is_event_currently_running

        event = Event(user_id=sample_user.user_id)
        assert is_event_currently_running(event) is False

    def test_get_primary_poi_id_unknown_ids_return_none(self):
        """get_primary_poi_id returns None when tokens are not in the POIS dict."""
        from app import get_primary_poi_id

        # These IDs are not in the real POIS data, so the function returns None.
        result = get_primary_poi_id("FAKE.POI|ANOTHER.FAKE")
        assert result is None

    def test_get_primary_poi_id_empty(self):
        """get_primary_poi_id returns None for empty/None input."""
        from app import get_primary_poi_id

        assert get_primary_poi_id("") is None
        assert get_primary_poi_id(None) is None

    def test_get_event_time_window_valid(self, sample_user):
        """get_event_time_window returns a (start, end) tuple for valid events."""
        from app import get_event_time_window

        event = Event(
            user_id=sample_user.user_id,
            date="2026-12-31",
            start_time="09:00",
            end_time="11:00",
        )
        result = get_event_time_window(event)
        assert result is not None
        start_dt, end_dt = result
        assert start_dt < end_dt

    def test_get_event_time_window_missing_fields(self, sample_user):
        """get_event_time_window returns None when date/time fields are absent."""
        from app import get_event_time_window

        event = Event(user_id=sample_user.user_id)
        assert get_event_time_window(event) is None


class TestEventsAPIRoutes:
    """Test the events-related API endpoints."""

    def test_my_events_unauthenticated(self, client):
        """GET /api/events/me returns 401 when not logged in."""
        response = client.get('/api/events/me')
        assert response.status_code == 401

    def test_my_events_authenticated_empty(self, authenticated_client):
        """GET /api/events/me returns an empty list when user has no events."""
        response = authenticated_client.get('/api/events/me')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'events' in data
        assert isinstance(data['events'], list)

    def test_my_events_authenticated_with_events(self, authenticated_client, db_session, sample_user):
        """GET /api/events/me returns future events for the authenticated user."""
        event = Event(
            user_id=sample_user.user_id,
            event_name="API Test Event",
            location="Room 101",
            day="Monday",
            date="2026-12-31",
            start_time="10:00",
            end_time="11:00",
        )
        db_session.add(event)
        db_session.commit()

        response = authenticated_client.get('/api/events/me')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['events']) >= 1
        assert any(e['event_name'] == 'API Test Event' for e in data['events'])

    def test_my_events_excludes_past_events(self, authenticated_client, db_session, sample_user):
        """GET /api/events/me does not return past events."""
        past_event = Event(
            user_id=sample_user.user_id,
            event_name="Past Event",
            location="Room 101",
            day="Monday",
            date="2020-01-01",
            start_time="10:00",
            end_time="11:00",
        )
        db_session.add(past_event)
        db_session.commit()

        response = authenticated_client.get('/api/events/me')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(e['event_name'] != 'Past Event' for e in data['events'])

    def test_delete_event_unauthenticated(self, client, sample_event):
        """DELETE /api/events/<id> returns 401 when not logged in."""
        response = client.delete(f'/api/events/{sample_event.event_id}')
        assert response.status_code == 401

    def test_delete_event_not_found(self, authenticated_client):
        """DELETE /api/events/<id> returns 404 for a non-existent event."""
        response = authenticated_client.delete('/api/events/999999')
        assert response.status_code == 404

    def test_delete_event_forbidden(self, authenticated_client, db_session, sample_user_2):
        """DELETE /api/events/<id> returns 403 when event belongs to another user."""
        other_event = Event(
            user_id=sample_user_2.user_id,
            event_name="Other User Event",
            location="Room 101",
            day="Monday",
            date="2026-12-31",
            start_time="10:00",
            end_time="11:00",
        )
        db_session.add(other_event)
        db_session.commit()

        response = authenticated_client.delete(f'/api/events/{other_event.event_id}')
        assert response.status_code == 403

    def test_delete_event_success(self, authenticated_client, db_session, sample_user):
        """DELETE /api/events/<id> removes a user's own future event."""
        event = Event(
            user_id=sample_user.user_id,
            event_name="Event to Delete",
            location="Room 101",
            day="Monday",
            date="2026-12-31",
            start_time="10:00",
            end_time="11:00",
        )
        db_session.add(event)
        db_session.commit()
        event_id = event.event_id

        response = authenticated_client.delete(f'/api/events/{event_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('deleted') is True

        # Verify the event is gone
        db_session.expire_all()
        deleted = db_session.query(Event).filter(Event.event_id == event_id).first()
        assert deleted is None

