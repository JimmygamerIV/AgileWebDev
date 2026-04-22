"""
Seed script for local development / testing.

Adds test users and sends pending friend requests to YOUR account, without
touching any existing data.

Usage:
    python seed.py <your_username>

Example:
    python seed.py joharalam_03

Prerequisite: sign up through the app first, then pass that username above.
"""

import sys
from werkzeug.security import generate_password_hash
from database import Session, init_db
from models import User, FriendRequest, Friend


TEST_USERS = [
    {"username": "john",  "nickname": "John Pork",              "email": "john@email.com"},
    {"username": "bombo", "nickname": "Bombardillo Crocadillo", "email": "croc@email.com"},
    {"username": "steve", "nickname": "Steve",                  "email": "steve@email.com"},
]

TEST_PASSWORD = "test1234"


def seed(target_username: str):
    init_db()
    db = Session()
    try:
        # Find the real user we're sending friend requests to
        me = db.query(User).filter(User.username == target_username).first()
        if me is None:
            print(f"ERROR: no user with username '{target_username}'. Sign up through the app first.")
            sys.exit(1)

        pw = generate_password_hash(TEST_PASSWORD, method="pbkdf2:sha256")

        # Insert test users only if they don't already exist
        added_users = []
        for u in TEST_USERS:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if existing is None:
                db.add(User(
                    username=u["username"],
                    nickname=u["nickname"],
                    email=u["email"],
                    password_hash=pw,
                ))
                added_users.append(u["username"])
        db.commit()

        # Send pending friend requests from each test user -> you,
        # but only if one doesn't already exist in any state.
        added_requests = 0
        for u in TEST_USERS:
            sender = db.query(User).filter(User.username == u["username"]).first()
            if sender is None or sender.user_id == me.user_id:
                continue

            # Skip if already friends
            already_friend = db.query(Friend).filter(
                Friend.user_id == me.user_id,
                Friend.friend_id == sender.user_id,
            ).first()
            if already_friend:
                continue

            # Skip if a request already exists either direction
            existing_req = db.query(FriendRequest).filter(
                ((FriendRequest.sender_id == sender.user_id) & (FriendRequest.receiver_id == me.user_id))
                | ((FriendRequest.sender_id == me.user_id) & (FriendRequest.receiver_id == sender.user_id))
            ).first()
            if existing_req:
                continue

            db.add(FriendRequest(
                sender_id=sender.user_id,
                receiver_id=me.user_id,
                status="pending",
            ))
            added_requests += 1
        db.commit()

        print(f"Target user: {me.username} (id={me.user_id})")
        print(f"Test users added: {added_users or 'none (already existed)'}")
        print(f"Friend requests added: {added_requests}")
        print(f"Test user password: {TEST_PASSWORD}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python seed.py <your_username>")
        sys.exit(1)
    seed(sys.argv[1])
