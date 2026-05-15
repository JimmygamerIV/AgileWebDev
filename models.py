from sqlalchemy import Column, Integer, Text, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base
from flask_login import UserMixin

Base = declarative_base()


class User(UserMixin, Base):
    """User model with Flask-Login integration.
    
    Attributes:
        user_id: Primary key, auto-incremented
        username: Unique username (max 15 chars)
        nickname: Display name (max 20 chars)
        email: Unique email for account recovery
        password_hash: Hashed password using pbkdf2:sha256
        timetable_link: URL to user's timetable
        avatar: User's avatar filename (default: "default.jpg")
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(15), nullable=False, unique=True)
    nickname = Column(String(20))
    email = Column(String(100), unique=True)
    password_hash = Column(Text, nullable=False)
    timetable_link = Column(Text)
    avatar = Column(String(100), default="default.jpg")

    def get_id(self):
        """Return user ID as string for Flask-Login session management."""
        return str(self.user_id)
    
    def __repr__(self):
        """String representation of User."""
        return f"<User {self.username} ({self.user_id})>"


class Friend(Base):
    __tablename__ = "friends"

    # Composite primary key
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    friend_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    is_favourite = Column(Integer, default=0)


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    request_id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    status = Column(String(8), nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'accepted', 'declined')"),
    )


class Event(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    event_name = Column(Text)
    location = Column(Text)
    day = Column(String(10))
    date = Column(Text)
    start_time = Column(Text)
    end_time = Column(Text)