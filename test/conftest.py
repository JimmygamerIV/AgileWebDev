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
from database import Base, Session,engine
from models import User, Friend, FriendRequest, Event

# Selenium imports
try:
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


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
    # Cookies returned by the test client are flagged secure-only by default
    # in flask-login (REMEMBER_COOKIE_SECURE=True), which breaks the test
    # client over plain HTTP. Disable that for tests.
    flask_app.config['REMEMBER_COOKIE_SECURE'] = False
    flask_app.config['SESSION_COOKIE_SECURE'] = False

    # Create a temporary test database
    fd, db_path = tempfile.mkstemp()
    os.close(fd)
    test_db_url = f'sqlite:///{db_path}'
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = test_db_url

    # CRITICAL: Reinitialize the database engine to use the test database URL.
    # Modules like app.py / auth.py / friends.py captured the `Session`
    # sessionmaker object at import time via `from database import Session`,
    # so REASSIGNING `database.Session` is not enough -- we must mutate the
    # *existing* sessionmaker so every importer sees the new engine.
    import database
    old_engine = database.engine
    new_engine = create_engine(test_db_url)
    database.engine = new_engine
    database.Session.configure(bind=new_engine)

    # Recreate all tables in the test database
    Base.metadata.drop_all(new_engine)
    Base.metadata.create_all(new_engine)

    yield flask_app

    # Cleanup: restore the original engine on the shared sessionmaker so
    # subsequent tests / production code aren't left pointing at a closed DB.
    new_engine.dispose()
    database.engine = old_engine
    database.Session.configure(bind=old_engine)
    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except OSError:
            pass


@pytest.fixture(scope="function")
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Create a CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(app):
    """
    """
    db = Session()
    
    yield db
    
    db.close()
    

    meta = Base.metadata
    with engine.connect() as connection:
        transaction = connection.begin()
        for table in reversed(meta.sorted_tables):
            connection.execute(table.delete())
        transaction.commit()


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


def _login_session(client, user):
    """Populate a test client's session so Flask-Login treats `user` as logged in.

    Flask-Login stores the authenticated user id under the ``_user_id`` key
    (not ``user_id``) and uses ``_fresh`` to track session freshness. Tests
    that previously set ``sess['user_id']`` were silently unauthenticated.
    """
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.user_id)
        sess['_fresh'] = True
        # Mirror the legacy key so any custom code still relying on it
        # continues to work in tests.
        sess['user_id'] = user.user_id


@pytest.fixture
def authenticated_client(app, client, sample_user):
    """Create an authenticated test client for user 1."""
    _login_session(client, sample_user)
    return client


@pytest.fixture
def authenticated_client_2(app, sample_user_2):
    """Create an independent authenticated test client for user 2."""
    client_2 = app.test_client()
    _login_session(client_2, sample_user_2)
    return client_2


@pytest.fixture
def authenticated_client_3(app, sample_user_3):
    """Create an independent authenticated test client for user 3."""
    client_3 = app.test_client()
    _login_session(client_3, sample_user_3)
    return client_3


# ===== Selenium Live Server Fixtures =====

@pytest.fixture(scope="function")
def live_server(app):
    """
    Create a live server for Selenium testing.
    
    This fixture starts a Flask development server on localhost
    and provides the URL for Selenium tests to connect to.
    """
    from werkzeug.serving import make_server
    import threading
    
    # Create and start the server
    server = make_server('127.0.0.1', 5000, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    # Small delay to ensure server is ready
    import time
    time.sleep(0.5)
    
    # pytest-flask's internal hooks access live_server.app, so we must
    # expose the Flask app on the yielded object even though we manage
    # the server ourselves.
    class LiveServer:
        url = "http://127.0.0.1:5000"
        app = flask_app  # satisfies pytest-flask hook attribute lookup

    yield LiveServer()
    
    # Shutdown the server
    server.shutdown()
    thread.join(timeout=5)
