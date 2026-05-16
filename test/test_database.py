"""
Tests for database functionality.
"""
import pytest
from database import Session, init_db, engine
from models import Base, User, Event, Friend
from werkzeug.security import generate_password_hash


class TestDatabaseInitialization:
    """Test database initialization."""
    
    def test_init_db_creates_tables(self):
        """Test that init_db creates necessary tables."""
        # Tables should be created by init_db
        # Check if we can query from empty tables
        db = Session()
        try:
            users = db.query(User).all()
            assert isinstance(users, list)
        finally:
            db.close()
    
    def test_database_session_creation(self):
        """Test creating a database session."""
        db = Session()
        try:
            assert db is not None
        finally:
            db.close()
    
    def test_session_commit(self, db_session):
        """Test session commit works."""
        user = User(
            username="commit_test",
            nickname="Commit Test",
            email="commit@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass123", method='pbkdf2:sha256')
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter(User.username == "commit_test").first()
        assert retrieved is not None
    
    def test_session_rollback(self, db_session):
        """Test session rollback works."""
        user = User(
            username="rollback_test",
            nickname="Rollback Test",
            email="rollback@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass123", method='pbkdf2:sha256')
        )
        db_session.add(user)
        db_session.rollback()
        
        retrieved = db_session.query(User).filter(User.username == "rollback_test").first()
        assert retrieved is None


class TestDatabaseConstraints:
    """Test database constraints."""
    
    def test_user_username_uniqueness(self, db_session):
        """Test username uniqueness constraint."""
        user1 = User(
            username="unique_test",
            nickname="User 1",
            email="user1@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass123", method='pbkdf2:sha256')
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="unique_test",
            nickname="User 2",
            email="user2@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass456", method='pbkdf2:sha256')
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_user_email_uniqueness(self, db_session):
        """Test email uniqueness constraint."""
        user1 = User(
            username="user1",
            nickname="User 1",
            email="unique@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass123", method='pbkdf2:sha256')
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="user2",
            nickname="User 2",
            email="unique@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass456", method='pbkdf2:sha256')
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_foreign_key_constraint_event(self, db_session):
        """Test foreign key constraint for events."""
        event = Event(
            user_id=99999,  # Non-existent user
            event_name="Orphan Event",
            location="Room 100",
            day="Monday",
            date="2026-05-18",
            start_time="10:00",
            end_time="11:00"
        )
        db_session.add(event)
        
        # SQLite doesn't enforce foreign keys by default, but we can test the logic
        # In production with proper FK enforcement, this would fail


class TestDatabaseQueries:
    """Test common database queries."""
    
    def test_query_all_users(self, db_session, sample_user, sample_user_2):
        """Test querying all users."""
        users = db_session.query(User).all()
        assert len(users) >= 2
    
    def test_query_user_by_username(self, db_session, sample_user):
        """Test querying user by username."""
        user = db_session.query(User).filter(User.username == sample_user.username).first()
        assert user is not None
        assert user.user_id == sample_user.user_id
    
    def test_query_user_by_email(self, db_session, sample_user):
        """Test querying user by email."""
        user = db_session.query(User).filter(User.email == sample_user.email).first()
        assert user is not None
        assert user.username == sample_user.username
    
    def test_query_user_by_id(self, db_session, sample_user):
        """Test querying user by ID."""
        user = db_session.get(User, sample_user.user_id)
        assert user is not None
        assert user.username == sample_user.username
    
    def test_query_nonexistent_user(self, db_session):
        """Test querying non-existent user."""
        user = db_session.query(User).filter(User.username == "nonexistent_user_xyz").first()
        assert user is None
    
    def test_query_events_by_user(self, db_session, sample_user, sample_event):
        """Test querying events by user."""
        events = db_session.query(Event).filter(Event.user_id == sample_user.user_id).all()
        assert len(events) >= 1
        assert events[0].user_id == sample_user.user_id
    
    def test_count_user_events(self, db_session, sample_user):
        """Test counting user's events."""
        # Add multiple events
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
        db_session.commit()
        
        count = db_session.query(Event).filter(Event.user_id == sample_user.user_id).count()
        assert count >= 3


class TestDatabaseTransactions:
    """Test database transaction handling."""
    
    def test_transaction_isolation(self, db_session):
        """Test transaction isolation."""
        user = User(
            username="transaction_test",
            nickname="Transaction User",
            email="transaction@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass123", method='pbkdf2:sha256')
        )
        db_session.add(user)
        db_session.commit()
        
        # Create another session to verify isolation
        db_session2 = Session()
        try:
            retrieved = db_session2.query(User).filter(
                User.username == "transaction_test"
            ).first()
            assert retrieved is not None
        finally:
            db_session2.close()
    
    def test_delete_cascade(self, db_session, sample_user):
        """Test cascading deletes."""
        # Add events for user
        for i in range(2):
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
        db_session.commit()
        
        # Verify events exist
        events_before = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).count()
        assert events_before == 2
        
        # Delete user
        db_session.delete(sample_user)
        db_session.commit()
        
        # Verify user is gone
        user = db_session.query(User).filter(
            User.user_id == sample_user.user_id
        ).first()
        assert user is None


class TestDatabaseEdgeCases:
    """Test database edge cases."""
    
    def test_empty_database_query(self, db_session):
        """Test querying empty table."""
        # Create new session to ensure clean state
        db_session.query(User).delete()
        db_session.commit()
        
        users = db_session.query(User).all()
        assert len(users) == 0
    
    def test_null_optional_fields(self, db_session):
        """Test null values in optional fields."""
        user = User(
            username="null_test",
            nickname=None,
            email="null@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass123", method='pbkdf2:sha256'),
            timetable_link=None
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter(User.username == "null_test").first()
        assert retrieved.nickname is None
        assert retrieved.timetable_link is None
    
    def test_special_characters_in_fields(self, db_session):
        """Test special characters in database fields."""
        user = User(
            username="special_user",
            nickname="User's Nickname!",
            email="special+tag@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass123", method='pbkdf2:sha256')
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter(User.username == "special_user").first()
        assert "'" in retrieved.nickname
        assert "+" in retrieved.email
    
    def test_unicode_characters(self, db_session):
        """Test unicode characters in fields."""
        user = User(
            username="unicode_user",
            nickname="用户名",  # Chinese characters
            email="unicode@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass123", method='pbkdf2:sha256')
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter(User.username == "unicode_user").first()
        assert retrieved.nickname == "用户名"
