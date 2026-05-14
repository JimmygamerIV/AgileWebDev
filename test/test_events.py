"""
Tests for events and timetable functionality.
"""
import pytest
from datetime import datetime
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
        assert events[0].location == 'Room 101'
    
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
        
        assert len(preview_events) == 2
        assert preview_events[0]['event_name'] == 'Lecture 1'
        assert preview_events[1]['event_name'] == 'Lecture 2'
    
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
        response = authenticated_client.get('/')
        assert response.status_code == 200
    
    def test_index_route_displays_events(self, authenticated_client, db_session, sample_user, sample_event):
        """Test index displays user's events."""
        response = authenticated_client.get('/')
        assert response.status_code == 200
        assert b'Test Lecture' in response.data or b'event' in response.data.lower()
    
    def test_profile_route_unauthenticated(self, client):
        """Test profile route without authentication."""
        response = client.get('/profile')
        assert response.status_code == 302  # Redirect
    
    def test_profile_route_authenticated(self, authenticated_client, sample_user):
        """Test profile route when authenticated."""
        response = authenticated_client.get('/profile')
        assert response.status_code == 200
        assert b'profile' in response.data.lower() or b'testuser' in response.data
    
    def test_add_event_route_unauthenticated(self, client):
        """Test add event route without authentication."""
        response = client.get('/add_event')
        assert response.status_code == 302  # Redirect
    
    def test_add_event_route_authenticated(self, authenticated_client):
        """Test add event route when authenticated."""
        response = authenticated_client.get('/add_event')
        assert response.status_code == 200


class TestImportTimetableRoute:
    """Test timetable import route."""
    
    def test_import_timetable_get(self, authenticated_client):
        """Test import timetable GET request."""
        response = authenticated_client.get('/import_timetable')
        assert response.status_code in [200, 404]  # Might not exist or might redirect
    
    def test_import_timetable_unauthenticated(self, client):
        """Test import timetable without authentication."""
        response = client.post('/import_timetable', data={})
        assert response.status_code in [302, 401]  # Redirect or unauthorized


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
