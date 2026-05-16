"""
Test utility functions and helpers.
"""
import tempfile
import os
from pathlib import Path


class TestHelpers:
    """Helper utilities for testing."""
    
    @staticmethod
    def create_test_ics_file(events_data):
        """Create a temporary ICS file for testing.
        
        Args:
            events_data: List of dicts with 'summary', 'location', 'dtstart', 'dtend'
        
        Returns:
            Path to temporary ICS file
        """
        ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//EN\n"
        
        for i, event in enumerate(events_data):
            ics_content += f"""BEGIN:VEVENT
SUMMARY:{event.get('summary', 'Event')}
DTSTART:{event.get('dtstart', '20260518T090000Z')}
DTEND:{event.get('dtend', '20260518T110000Z')}
LOCATION:{event.get('location', '')}
UID:test-event-{i}@example.com
END:VEVENT
"""
        
        ics_content += "END:VCALENDAR"
        
        fd, path = tempfile.mkstemp(suffix='.ics')
        os.write(fd, ics_content.encode())
        os.close(fd)
        
        return path
    
    @staticmethod
    def cleanup_temp_file(filepath):
        """Clean up temporary file."""
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
        except Exception:
            pass
    
    @staticmethod
    def generate_valid_uwa_emails(count=5):
        """Generate valid UWA email addresses for testing.
        
        Args:
            count: Number of emails to generate
        
        Returns:
            List of valid UWA email addresses
        """
        emails = []
        for i in range(count):
            emails.append(f"student{i}@student.uwa.edu.au")
        return emails
    
    @staticmethod
    def generate_invalid_emails(count=3):
        """Generate invalid email addresses for testing.
        
        Returns:
            List of invalid email addresses
        """
        return [
            "invalid.email",
            "user@gmail.com",
            "notauwa@domain.com",
            "@student.uwa.edu.au",
            "user@.edu.au"
        ][:count]
    
    @staticmethod
    def generate_valid_passwords(count=3):
        """Generate valid passwords meeting requirements.
        
        Requirements:
        - At least 6 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains number
        
        Returns:
            List of valid passwords
        """
        return [
            "ValidPass1",
            "SecurePass123",
            "TestPassword456",
            "MyPass789",
            "UnicodePass中123"
        ][:count]
    
    @staticmethod
    def generate_invalid_passwords():
        """Generate invalid passwords for testing.
        
        Returns:
            Dict mapping invalid password to reason
        """
        return {
            "short1": "Too short",
            "nouppercase123": "No uppercase",
            "NOLOWERCASE123": "No lowercase",
            "NoNumbers": "No numbers",
            "ValidPass1": "Valid password for comparison"
        }


class RequestHelpers:
    """Helper utilities for HTTP requests in tests."""
    
    @staticmethod
    def create_signup_data(username="newuser", email="new@student.uwa.edu.au",
                          password="ValidPass123", **kwargs):
        """Create signup form data.
        
        Args:
            username: Username for signup
            email: Email address
            password: Password
            **kwargs: Additional fields
        
        Returns:
            Dict with signup form data
        """
        data = {
            'username': username,
            'nickname': kwargs.get('nickname', 'Test User'),
            'password': password,
            'confirm_password': kwargs.get('confirm_password', password),
            'email': email,
            'csrf_token': kwargs.get('csrf_token', 'dummy')
        }
        return data
    
    @staticmethod
    def create_signin_data(username="testuser", password="TestPass123", **kwargs):
        """Create signin form data.
        
        Args:
            username: Username for signin
            password: Password
            **kwargs: Additional fields
        
        Returns:
            Dict with signin form data
        """
        data = {
            'username': username,
            'password': password,
            'csrf_token': kwargs.get('csrf_token', 'dummy')
        }
        return data
    
    @staticmethod
    def create_add_friend_data(target_username="friend", **kwargs):
        """Create add friend form data.
        
        Args:
            target_username: Friend username
            **kwargs: Additional fields
        
        Returns:
            Dict with add friend form data
        """
        data = {
            'target_username': target_username,
            'csrf_token': kwargs.get('csrf_token', 'dummy')
        }
        return data


class DatabaseHelpers:
    """Helper utilities for database operations in tests."""
    
    @staticmethod
    def count_users(db_session):
        """Count total users in database."""
        from models import User
        return db_session.query(User).count()
    
    @staticmethod
    def count_events(db_session, user_id=None):
        """Count events, optionally for specific user."""
        from models import Event
        query = db_session.query(Event)
        if user_id:
            query = query.filter(Event.user_id == user_id)
        return query.count()
    
    @staticmethod
    def count_friends(db_session, user_id):
        """Count friends for a user."""
        from models import Friend
        return db_session.query(Friend).filter(
            (Friend.user_id == user_id) | (Friend.friend_id == user_id)
        ).count()
    
    @staticmethod
    def count_friend_requests(db_session, user_id=None, status="pending"):
        """Count friend requests."""
        from models import FriendRequest
        query = db_session.query(FriendRequest)
        if user_id:
            query = query.filter(
                (FriendRequest.sender_id == user_id) |
                (FriendRequest.receiver_id == user_id)
            )
        if status:
            query = query.filter(FriendRequest.status == status)
        return query.count()
    
    @staticmethod
    def clear_all_data(db_session):
        """Clear all data from database (use with caution!)."""
        from models import Event, FriendRequest, Friend, User
        
        db_session.query(Event).delete()
        db_session.query(FriendRequest).delete()
        db_session.query(Friend).delete()
        db_session.query(User).delete()
        db_session.commit()


class AssertionHelpers:
    """Custom assertion helpers for tests."""
    
    @staticmethod
    def assert_user_exists(db_session, username):
        """Assert user exists in database."""
        from models import User
        user = db_session.query(User).filter(User.username == username).first()
        assert user is not None, f"User {username} not found in database"
        return user
    
    @staticmethod
    def assert_user_not_exists(db_session, username):
        """Assert user does not exist in database."""
        from models import User
        user = db_session.query(User).filter(User.username == username).first()
        assert user is None, f"User {username} found in database but should not exist"
    
    @staticmethod
    def assert_event_exists(db_session, event_name, user_id):
        """Assert event exists for user."""
        from models import Event
        event = db_session.query(Event).filter(
            Event.event_name == event_name,
            Event.user_id == user_id
        ).first()
        assert event is not None, f"Event {event_name} not found for user {user_id}"
        return event
    
    @staticmethod
    def assert_friends(db_session, user_id1, user_id2):
        """Assert two users are friends."""
        from models import Friend
        friendship = db_session.query(Friend).filter(
            (Friend.user_id == user_id1 and Friend.friend_id == user_id2) |
            (Friend.user_id == user_id2 and Friend.friend_id == user_id1)
        ).first()
        assert friendship is not None, f"Users {user_id1} and {user_id2} are not friends"
        return friendship
    
    @staticmethod
    def assert_not_friends(db_session, user_id1, user_id2):
        """Assert two users are not friends."""
        from models import Friend
        friendship = db_session.query(Friend).filter(
            (Friend.user_id == user_id1 and Friend.friend_id == user_id2) |
            (Friend.user_id == user_id2 and Friend.friend_id == user_id1)
        ).first()
        assert friendship is None, f"Users {user_id1} and {user_id2} are friends but should not be"


# Usage examples in docstrings
"""
# In your tests:

from test.test_utils import TestHelpers, RequestHelpers, DatabaseHelpers, AssertionHelpers

# Create test ICS file
ics_path = TestHelpers.create_test_ics_file([
    {'summary': 'Lecture 1', 'location': 'Room 101'},
    {'summary': 'Lecture 2', 'location': 'Room 102'}
])

# Generate signup data
signup_data = RequestHelpers.create_signup_data(
    username="testuser",
    email="test@student.uwa.edu.au"
)

# Count users
user_count = DatabaseHelpers.count_users(db_session)

# Assert user exists
user = AssertionHelpers.assert_user_exists(db_session, "testuser")

# Clean up
TestHelpers.cleanup_temp_file(ics_path)
"""
