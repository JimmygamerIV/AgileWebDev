"""
Pytest configuration and fixtures for the UniMap application.
"""
import os
import tempfile
import pytest
from pathlib import Path
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app as flask_app
from database import Base, Session
from models import User, Friend, FriendRequest, Event


@pytest.fixture(scope="function")
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp()
    os.close(fd)
    
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    
    TestSession = sessionmaker(bind=engine)
    
    yield engine, TestSession
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture(scope="function")
def app():
    """Create application for testing."""
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    
    # Use in-memory SQLite for tests
    fd, db_path = tempfile.mkstemp()
    os.close(fd)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    # Recreate database for tests
    from database import engine
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    yield flask_app
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(scope="function")
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Create a CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """Create a database session for testing."""
    db = Session()
    yield db
    db.close()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        username="testuser",
        nickname="Test User",
        email="testuser@student.uwa.edu.au",
        password_hash=generate_password_hash("TestPass123", method='pbkdf2:sha256')
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_user_2(db_session):
    """Create a second sample user for testing."""
    user = User(
        username="testuser2",
        nickname="Test User 2",
        email="testuser2@student.uwa.edu.au",
        password_hash=generate_password_hash("TestPass456", method='pbkdf2:sha256')
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_user_3(db_session):
    """Create a third sample user for testing."""
    user = User(
        username="testuser3",
        nickname="Test User 3",
        email="testuser3@student.uwa.edu.au",
        password_hash=generate_password_hash("TestPass789", method='pbkdf2:sha256')
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_event(db_session, sample_user):
    """Create a sample event for testing."""
    event = Event(
        user_id=sample_user.user_id,
        event_name="Test Lecture",
        location="Room 101",
        day="Monday",
        date="2026-05-18",
        start_time="09:00",
        end_time="11:00"
    )
    db_session.add(event)
    db_session.commit()
    return event


@pytest.fixture
def authenticated_client(client, sample_user):
    """Create an authenticated test client."""
    with client:
        # Manually set session
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.user_id
    return client
