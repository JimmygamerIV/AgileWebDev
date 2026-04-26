
import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import app
from database import init_db, Session, engine
import pytest
from models import User

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.test_client() as client:
        yield client


@pytest.fixture
def db_session():
    init_db()
    db = Session()
    yield db
    db.close()

import uuid

@pytest.fixture
def logged_in_client(client, db_session):
    user = User(
        username=f"testuser_{uuid.uuid4().hex[:6]}",
        nickname="Tester",
        password_hash="fakehashedpassword"
    )

    db_session.add(user)
    db_session.commit()

    with client.session_transaction() as sess:
        sess["user_id"] = user.user_id

    return client, user