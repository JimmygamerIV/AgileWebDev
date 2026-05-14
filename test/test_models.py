"""
Tests for database models.
"""
import pytest
from models import User, Friend, FriendRequest, Event
from werkzeug.security import check_password_hash, generate_password_hash


class TestUserModel:
    """Test User model."""
    
    def test_user_creation(self, db_session):
        """Test creating a user."""
        user = User(
            username="john_doe",
            nickname="John",
            email="john@student.uwa.edu.au",
            password_hash=generate_password_hash("SecurePass123", method='pbkdf2:sha256')
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.user_id is not None
        assert user.username == "john_doe"
        assert user.nickname == "John"
        assert user.email == "john@student.uwa.edu.au"
        assert check_password_hash(user.password_hash, "SecurePass123")
    
    def test_user_unique_username(self, db_session):
        """Test username uniqueness constraint."""
        user1 = User(
            username="duplicate",
            nickname="User 1",
            email="user1@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass123", method='pbkdf2:sha256')
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="duplicate",
            nickname="User 2",
            email="user2@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass456", method='pbkdf2:sha256')
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_user_unique_email(self, db_session):
        """Test email uniqueness constraint."""
        user1 = User(
            username="user1",
            nickname="User 1",
            email="duplicate@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass123", method='pbkdf2:sha256')
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="user2",
            nickname="User 2",
            email="duplicate@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass456", method='pbkdf2:sha256')
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


class TestFriendModel:
    """Test Friend model."""
    
    def test_friend_creation(self, db_session, sample_user, sample_user_2):
        """Test creating a friend relationship."""
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id
        )
        db_session.add(friend)
        db_session.commit()
        
        assert friend.user_id == sample_user.user_id
        assert friend.friend_id == sample_user_2.user_id
        assert friend.is_favourite == 0
    
    def test_friend_favourite(self, db_session, sample_user, sample_user_2):
        """Test marking friend as favourite."""
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id,
            is_favourite=1
        )
        db_session.add(friend)
        db_session.commit()
        
        assert friend.is_favourite == 1
    
    def test_friend_composite_key(self, db_session, sample_user, sample_user_2):
        """Test friend composite primary key."""
        friend1 = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id
        )
        friend2 = Friend(
            user_id=sample_user_2.user_id,
            friend_id=sample_user.user_id
        )
        db_session.add(friend1)
        db_session.add(friend2)
        db_session.commit()
        
        # Should be able to have different relationships from each direction
        retrieved = db_session.query(Friend).filter(
            Friend.user_id == sample_user.user_id,
            Friend.friend_id == sample_user_2.user_id
        ).first()
        assert retrieved is not None


class TestFriendRequestModel:
    """Test FriendRequest model."""
    
    def test_friend_request_creation(self, db_session, sample_user, sample_user_2):
        """Test creating a friend request."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status="pending"
        )
        db_session.add(req)
        db_session.commit()
        
        assert req.request_id is not None
        assert req.sender_id == sample_user.user_id
        assert req.receiver_id == sample_user_2.user_id
        assert req.status == "pending"
    
    def test_friend_request_status_pending(self, db_session, sample_user, sample_user_2):
        """Test friend request with pending status."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status="pending"
        )
        db_session.add(req)
        db_session.commit()
        
        assert req.status == "pending"
    
    def test_friend_request_status_accepted(self, db_session, sample_user, sample_user_2):
        """Test friend request with accepted status."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status="accepted"
        )
        db_session.add(req)
        db_session.commit()
        
        assert req.status == "accepted"
    
    def test_friend_request_status_declined(self, db_session, sample_user, sample_user_2):
        """Test friend request with declined status."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status="declined"
        )
        db_session.add(req)
        db_session.commit()
        
        assert req.status == "declined"
    
    def test_friend_request_invalid_status(self, db_session, sample_user, sample_user_2):
        """Test friend request with invalid status."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status="invalid"
        )
        db_session.add(req)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


class TestEventModel:
    """Test Event model."""
    
    def test_event_creation(self, db_session, sample_user):
        """Test creating an event."""
        event = Event(
            user_id=sample_user.user_id,
            event_name="Lecture",
            location="Lecture Hall A",
            day="Monday",
            date="2026-05-18",
            start_time="09:00",
            end_time="11:00"
        )
        db_session.add(event)
        db_session.commit()
        
        assert event.event_id is not None
        assert event.user_id == sample_user.user_id
        assert event.event_name == "Lecture"
        assert event.location == "Lecture Hall A"
        assert event.day == "Monday"
        assert event.date == "2026-05-18"
        assert event.start_time == "09:00"
        assert event.end_time == "11:00"
    
    def test_event_multiple_per_user(self, db_session, sample_user):
        """Test user can have multiple events."""
        event1 = Event(
            user_id=sample_user.user_id,
            event_name="Lecture 1",
            location="Room 101",
            day="Monday",
            date="2026-05-18",
            start_time="09:00",
            end_time="11:00"
        )
        event2 = Event(
            user_id=sample_user.user_id,
            event_name="Lecture 2",
            location="Room 102",
            day="Tuesday",
            date="2026-05-19",
            start_time="14:00",
            end_time="16:00"
        )
        db_session.add(event1)
        db_session.add(event2)
        db_session.commit()
        
        events = db_session.query(Event).filter(Event.user_id == sample_user.user_id).all()
        assert len(events) == 2
    
    def test_event_optional_fields(self, db_session, sample_user):
        """Test event with optional fields."""
        event = Event(
            user_id=sample_user.user_id,
            event_name=None,
            location=None,
            day=None,
            date=None,
            start_time=None,
            end_time=None
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(Event.event_id == event.event_id).first()
        assert retrieved is not None
        assert retrieved.event_name is None
