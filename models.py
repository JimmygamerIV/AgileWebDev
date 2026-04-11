from sqlalchemy import Column, Integer, Text, String, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(15), nullable=False, unique=True)
    nickname = Column(String(20))
    password_hash =  Column(Text, nullable=False)
    timetable_link = Column(Text)


class Friend(Base):
    __tablename__ = "friends"

    # Composite primary key
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    friend_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)


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
    start_time = Column(Text)
    end_time = Column(Text)