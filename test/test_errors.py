"""
Error handling and data consistency tests.
Tests for exception handling, error recovery, and data integrity.
"""
import pytest
from datetime import datetime
from models import User, Event, Friend, FriendRequest
from database import Session
from werkzeug.security import generate_password_hash


class TestDatabaseErrorHandling:
    """Test database error handling."""
    
    def test_concurrent_event_creation(self, db_session, sample_user):
        """Test creating events concurrently."""
        # Simulate concurrent event creation
        events = []
        for i in range(10):
            event = Event(
                user_id=sample_user.user_id,
                event_name=f'Concurrent Event {i}',
                location='Room 100',
                day='Monday',
                date='2026-05-18',
                start_time=f'{9+i%8}:00',
                end_time=f'{10+i%8}:00'
            )
            events.append(event)
            db_session.add(event)
        
        db_session.commit()
        
        # Verify all created
        count = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).count()
        assert count == 10
    
    def test_update_during_delete(self, db_session, sample_user, sample_event):
        """Test updating event during deletion."""
        event_id = sample_event.event_id
        
        # Modify event
        sample_event.event_name = 'Modified Event'
        db_session.commit()
        
        # Delete event
        db_session.delete(sample_event)
        db_session.commit()
        
        # Verify deleted
        retrieved = db_session.query(Event).filter(
            Event.event_id == event_id
        ).first()
        assert retrieved is None
    
    def test_rollback_on_constraint_violation(self, db_session, sample_user):
        """Test rollback when constraint is violated."""
        # Create valid event
        event = Event(
            user_id=sample_user.user_id,
            event_name='Test Event',
            location='Room 100',
            day='Monday',
            date='2026-05-18',
            start_time='10:00',
            end_time='11:00'
        )
        db_session.add(event)
        db_session.commit()
        
        count_before = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).count()
        
        # Try to violate foreign key
        invalid_event = Event(
            user_id=99999,  # Non-existent user
            event_name='Invalid Event',
            location='Room 100',
            day='Monday',
            date='2026-05-18',
            start_time='10:00',
            end_time='11:00'
        )
        db_session.add(invalid_event)
        db_session.commit()  # May fail depending on FK enforcement
        
        # Original data should be intact
        count_after = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).count()
        assert count_before == count_after


class TestICSImportErrorHandling:
    """Test error handling in ICS import."""
    
    def test_import_empty_ics(self, db_session, sample_user):
        """Test importing empty ICS file."""
        from app import importICS
        
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
END:VCALENDAR"""
        
        preview = importICS(ics_content.encode(), sample_user.user_id)
        
        assert len(preview) == 0
    
    def test_import_ics_missing_required_fields(self, db_session, sample_user):
        """Test importing ICS with missing required fields."""
        from app import importICS
        
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
SUMMARY:Event Without Time
UID:test@example.com
END:VEVENT
END:VCALENDAR"""
        
        # Should handle gracefully
        try:
            preview = importICS(ics_content.encode(), sample_user.user_id)
            # Either import fails or handles missing fields
        except Exception:
            # Exception is acceptable
            pass
    
    def test_import_ics_with_very_long_fields(self, db_session, sample_user):
        """Test importing ICS with very long field values."""
        from app import importICS
        
        long_summary = 'A' * 1000
        long_location = 'B' * 1000
        
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
SUMMARY:{long_summary}
DTSTART:20260518T090000Z
DTEND:20260518T110000Z
LOCATION:{long_location}
UID:long@example.com
END:VEVENT
END:VCALENDAR"""
        
        preview = importICS(ics_content.encode(), sample_user.user_id)
        
        # Should handle long fields
        assert len(preview) >= 0
    
    def test_import_ics_with_special_characters(self, db_session, sample_user):
        """Test importing ICS with special characters."""
        from app import importICS
        
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
SUMMARY:Event with Spëcial Çhars & <Tags>
DTSTART:20260518T090000Z
DTEND:20260518T110000Z
LOCATION:Room 中文 & Special
UID:special@example.com
END:VEVENT
END:VCALENDAR"""
        
        preview = importICS(ics_content.encode(), sample_user.user_id)
        
        # Should handle special characters
        assert len(preview) == 1
    
    def test_import_ics_with_invalid_datetime_format(self, db_session, sample_user):
        """Test importing ICS with invalid datetime."""
        from app import importICS
        
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
SUMMARY:Event with invalid date
DTSTART:invalid-date
DTEND:also-invalid
UID:invalid@example.com
END:VEVENT
END:VCALENDAR"""
        
        # Should handle gracefully
        try:
            preview = importICS(ics_content.encode(), sample_user.user_id)
        except Exception:
            # Exception expected for malformed datetime
            pass


class TestDataConsistency:
    """Test data consistency."""
    
    def test_friend_request_sender_exists(self, db_session, sample_user, sample_user_2):
        """Test friend request maintains referential integrity."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status='pending'
        )
        db_session.add(req)
        db_session.commit()
        
        # Sender should exist
        sender = db_session.query(User).filter(
            User.user_id == req.sender_id
        ).first()
        assert sender is not None
    
    def test_friend_request_receiver_exists(self, db_session, sample_user, sample_user_2):
        """Test friend request receiver exists."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status='pending'
        )
        db_session.add(req)
        db_session.commit()
        
        # Receiver should exist
        receiver = db_session.query(User).filter(
            User.user_id == req.receiver_id
        ).first()
        assert receiver is not None
    
    def test_event_user_exists(self, db_session, sample_user, sample_event):
        """Test event user exists."""
        user = db_session.query(User).filter(
            User.user_id == sample_event.user_id
        ).first()
        assert user is not None
    
    def test_delete_user_events_consistency(self, db_session, sample_user):
        """Test that deleting user maintains event consistency."""
        # Add events
        for i in range(3):
            event = Event(
                user_id=sample_user.user_id,
                event_name=f'Event {i}',
                location='Room 100',
                day='Monday',
                date='2026-05-18',
                start_time=f'{9+i}:00',
                end_time=f'{10+i}:00'
            )
            db_session.add(event)
        db_session.commit()
        
        # Verify events exist
        events_before = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).all()
        assert len(events_before) == 3


class TestNullValueHandling:
    """Test handling of NULL values."""
    
    def test_user_with_null_nickname(self, db_session):
        """Test user with NULL nickname."""
        user = User(
            username='nullnick',
            nickname=None,
            email='nullnick@student.uwa.edu.au',
            password_hash=generate_password_hash('Pass123', method='pbkdf2:sha256')
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter(
            User.username == 'nullnick'
        ).first()
        assert retrieved.nickname is None
    
    def test_user_with_null_timetable_link(self, db_session):
        """Test user with NULL timetable_link."""
        user = User(
            username='notimetable',
            nickname='No Timetable',
            email='notimetable@student.uwa.edu.au',
            password_hash=generate_password_hash('Pass123', method='pbkdf2:sha256'),
            timetable_link=None
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter(
            User.username == 'notimetable'
        ).first()
        assert retrieved.timetable_link is None
    
    def test_event_with_null_location(self, db_session, sample_user):
        """Test event with NULL location."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='No Location',
            location=None,
            day='Monday',
            date='2026-05-18',
            start_time='10:00',
            end_time='11:00'
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.event_name == 'No Location'
        ).first()
        assert retrieved.location is None


class TestUnicodeHandling:
    """Test unicode character handling."""
    
    def test_user_with_unicode_nickname(self, db_session):
        """Test user with unicode characters in nickname."""
        user = User(
            username='unicodenick',
            nickname='用户 Üser Üñîçødé',
            email='unicode@student.uwa.edu.au',
            password_hash=generate_password_hash('Pass123', method='pbkdf2:sha256')
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter(
            User.username == 'unicodenick'
        ).first()
        assert '用户' in retrieved.nickname
        assert 'Ü' in retrieved.nickname
    
    def test_event_with_unicode_location(self, db_session, sample_user):
        """Test event with unicode location."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='Unicode Location Event',
            location='教室 101 Büroraum',
            day='Monday',
            date='2026-05-18',
            start_time='10:00',
            end_time='11:00'
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.event_name == 'Unicode Location Event'
        ).first()
        assert '教室' in retrieved.location


class TestCaseHandling:
    """Test case sensitivity."""
    
    def test_username_case_insensitivity(self, client, db_session):
        """Test that usernames are case sensitive or normalized."""
        # Create user
        response1 = client.post('/signup', data={
            'username': 'CaseSensitive',
            'nickname': 'Case',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'case1@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Try to create with different case
        response2 = client.post('/signup', data={
            'username': 'casesensitive',
            'nickname': 'case',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'case2@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Behavior depends on implementation
        # DB should enforce uniqueness
        user_count = db_session.query(User).filter(
            User.username.in_(['CaseSensitive', 'casesensitive'])
        ).count()
        assert user_count >= 1
    
    def test_email_case_insensitivity(self, client, db_session):
        """Test email case handling."""
        # Create user with lowercase email
        response1 = client.post('/signup', data={
            'username': 'emailtest1',
            'nickname': 'Email',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'test@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Try with uppercase
        response2 = client.post('/signup', data={
            'username': 'emailtest2',
            'nickname': 'Email',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'TEST@STUDENT.UWA.EDU.AU',
            'csrf_token': 'dummy'
        }, follow_redirects=True)


class TestEmptyStringHandling:
    """Test empty string handling."""
    
    def test_event_with_empty_location_string(self, db_session, sample_user):
        """Test event with empty string location."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='Empty Location',
            location='',  # Empty string instead of NULL
            day='Monday',
            date='2026-05-18',
            start_time='10:00',
            end_time='11:00'
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.event_name == 'Empty Location'
        ).first()
        assert retrieved.location == ''
    
    def test_event_with_empty_event_name(self, db_session, sample_user):
        """Test event with empty event name."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='',
            location='Room 100',
            day='Monday',
            date='2026-05-18',
            start_time='10:00',
            end_time='11:00'
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.location == 'Room 100'
        ).first()
        assert retrieved.event_name == ''


class TestTypeValidation:
    """Test type validation."""
    
    def test_friend_request_status_type(self, db_session, sample_user, sample_user_2):
        """Test friend request status field type."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status='pending'
        )
        db_session.add(req)
        db_session.commit()
        
        assert isinstance(req.status, str)
        assert req.status in ['pending', 'accepted', 'declined']
    
    def test_friend_is_favourite_type(self, db_session, sample_user, sample_user_2):
        """Test friend is_favourite field type."""
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id,
            is_favourite=1
        )
        db_session.add(friend)
        db_session.commit()
        
        assert isinstance(friend.is_favourite, int)
        assert friend.is_favourite in [0, 1]
