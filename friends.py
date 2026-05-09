from flask import Blueprint, g, redirect, render_template, session, request, jsonify
from database import Session
from models import User, Friend, FriendRequest
from forms import AddFriendForm, FriendActionForm
from datetime import date, datetime
from models import Event, User

friends_bp = Blueprint("friends", __name__)


def get_friend_ids(db, user_id):
    rows = db.query(Friend).filter(
        (Friend.user_id == user_id) | (Friend.friend_id == user_id)
    ).all()

    friend_ids = set()
    for row in rows:
        if row.user_id == user_id:
            friend_ids.add(row.friend_id)
        if row.friend_id == user_id:
            friend_ids.add(row.user_id)

    return friend_ids


def build_friends_list(db, user_id):
    friend_rows = db.query(Friend).filter(Friend.user_id == user_id).all()
    friends_list = []

    if friend_rows:
        friend_ids = [row.friend_id for row in friend_rows]
        users = db.query(User).filter(User.user_id.in_(friend_ids)).all()
        users_by_id = {user.user_id: user for user in users}

        for row in friend_rows:
            friend_user = users_by_id.get(row.friend_id)
            if not friend_user:
                continue
            friend_user.is_favourite = bool(row.is_favourite)
            friends_list.append(friend_user)
    else:
        friend_ids = get_friend_ids(db, user_id)
        friends_list = db.query(User).filter(User.user_id.in_(friend_ids)).all()
        for friend_user in friends_list:
            friend_user.is_favourite = False

    friends_list.sort(
        key=lambda user: (
            0 if getattr(user, "is_favourite", False) else 1,
            (user.nickname or user.username or "").lower(),
        )
    )

    return friends_list


@friends_bp.route("/friends")
def friends():
    if g.current_user is None:
        return redirect("/signin")

    add_form = AddFriendForm()
    action_form = FriendActionForm()
    db = Session()
    try:
        user_id = session["user_id"]

        friends_list = build_friends_list(db, user_id)

        incoming_rows = db.query(FriendRequest).filter(
            FriendRequest.receiver_id == user_id,
            FriendRequest.status == "pending",
        ).all()

        incoming_sender_ids = [row.sender_id for row in incoming_rows]
        incoming_users = db.query(User).filter(User.user_id.in_(incoming_sender_ids)).all()
        incoming_users_by_id = {user.user_id: user for user in incoming_users}

        incoming_requests = []
        for row in incoming_rows:
            sender = incoming_users_by_id.get(row.sender_id)
            if not sender:
                continue
            incoming_requests.append(
                {
                    "request_id": row.request_id,
                    "user_id": sender.user_id,
                    "username": sender.username,
                    "nickname": sender.nickname,
                }
            )

        outgoing_rows = db.query(FriendRequest).filter(
            FriendRequest.sender_id == user_id,
            FriendRequest.status == "pending",
        ).all()

        outgoing_receiver_ids = [row.receiver_id for row in outgoing_rows]
        outgoing_users = db.query(User).filter(User.user_id.in_(outgoing_receiver_ids)).all()
        outgoing_users_by_id = {user.user_id: user for user in outgoing_users}

        outgoing_requests = []
        for row in outgoing_rows:
            receiver = outgoing_users_by_id.get(row.receiver_id)
            if not receiver:
                continue
            outgoing_requests.append(
                {
                    "request_id": row.request_id,
                    "user_id": receiver.user_id,
                    "username": receiver.username,
                    "nickname": receiver.nickname,
                }
            )

        return render_template(
            "friends.html",
            friends=friends_list,
            incoming_requests=incoming_requests,
            outgoing_requests=outgoing_requests,
            add_form=add_form,
            action_form=action_form,
            show_full_nav=True,
        )
    finally:
        db.close()


@friends_bp.route("/favourite_friend", methods=["POST"])
def favourite_friend():
    if g.current_user is None:
        return jsonify({"error": "Not authenticated"}), 401

    db = Session()
    try:
        user_id = session["user_id"]
        friend_id = request.form.get("friend_id", type=int)

        if not friend_id:
            return jsonify({"error": "Missing friend id"}), 400

        friend_row = db.query(Friend).filter(
            Friend.user_id == user_id,
            Friend.friend_id == friend_id,
        ).first()

        if friend_row is None:
            # Fall back to legacy single-row friendships.
            legacy_row = db.query(Friend).filter(
                Friend.user_id == friend_id,
                Friend.friend_id == user_id,
            ).first()
            if legacy_row is None:
                return jsonify({"error": "Friend not found"}), 404

            friend_row = Friend(user_id=user_id, friend_id=friend_id, is_favourite=0)
            db.add(friend_row)

        friend_row.is_favourite = 0 if friend_row.is_favourite else 1
        db.commit()

        return jsonify({"success": True, "is_favourite": bool(friend_row.is_favourite)})
    finally:
        db.close()


@friends_bp.route("/remove_friend", methods=["POST"])
def remove_friend():
    if g.current_user is None:
        return jsonify({"error": "Not authenticated"}), 401

    db = Session()
    try:
        user_id = session["user_id"]
        friend_id = request.form.get("friend_id", type=int)

        if not friend_id:
            return jsonify({"error": "Missing friend id"}), 400

        db.query(Friend).filter(
            ((Friend.user_id == user_id) & (Friend.friend_id == friend_id))
            | ((Friend.user_id == friend_id) & (Friend.friend_id == user_id))
        ).delete()

        db.query(FriendRequest).filter(
            ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == friend_id))
            | ((FriendRequest.sender_id == friend_id) & (FriendRequest.receiver_id == user_id))
        ).delete()

        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()


@friends_bp.route("/accept_request", methods=["POST"])
def accept_request():
    if g.current_user is None:
        return jsonify({"error": "Not authenticated"}), 401

    db = Session()
    try:
        user_id = session["user_id"]
        request_id = request.form.get("request_id", type=int)
        sender_id = request.form.get("sender_id", type=int)

        if not request_id or not sender_id:
            return jsonify({"error": "Missing request data"}), 400

        friend_request = db.query(FriendRequest).filter(
            FriendRequest.request_id == request_id,
            FriendRequest.receiver_id == user_id,
            FriendRequest.status == "pending",
        ).first()

        if friend_request is None:
            return jsonify({"error": "Request not found"}), 404

        friend_request.status = "accepted"

        existing = db.query(Friend).filter(
            Friend.user_id == user_id,
            Friend.friend_id == sender_id,
        ).first()
        if existing is None:
            db.add(Friend(user_id=user_id, friend_id=sender_id, is_favourite=0))

        reverse_existing = db.query(Friend).filter(
            Friend.user_id == sender_id,
            Friend.friend_id == user_id,
        ).first()
        if reverse_existing is None:
            db.add(Friend(user_id=sender_id, friend_id=user_id, is_favourite=0))

        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()


@friends_bp.route("/reject_request", methods=["POST"])
def reject_request():
    if g.current_user is None:
        return jsonify({"error": "Not authenticated"}), 401

    db = Session()
    try:
        user_id = session["user_id"]
        request_id = request.form.get("request_id", type=int)

        if not request_id:
            return jsonify({"error": "Missing request id"}), 400

        friend_request = db.query(FriendRequest).filter(
            FriendRequest.request_id == request_id,
            FriendRequest.receiver_id == user_id,
            FriendRequest.status == "pending",
        ).first()

        if friend_request is None:
            return jsonify({"error": "Request not found"}), 404

        friend_request.status = "declined"
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()


@friends_bp.route("/cancel_request", methods=["POST"])
def cancel_request():
    if g.current_user is None:
        return jsonify({"error": "Not authenticated"}), 401

    db = Session()
    try:
        user_id = session["user_id"]
        request_id = request.form.get("request_id", type=int)

        if not request_id:
            return jsonify({"error": "Missing request id"}), 400

        db.query(FriendRequest).filter(
            FriendRequest.request_id == request_id,
            FriendRequest.sender_id == user_id,
            FriendRequest.status == "pending",
        ).delete()

        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()


@friends_bp.route("/search_users", methods=["GET"])
def search_users():
    if g.current_user is None:
        return jsonify({"error": "Not authenticated"}), 401

    db = Session()
    try:
        user_id = session["user_id"]
        query = (request.args.get("q") or "").strip()

        if len(query) < 2:
            return jsonify([])

        friend_ids = get_friend_ids(db, user_id)

        users = db.query(User).filter(
            User.username.ilike(f"%{query}%"),
            User.user_id != user_id,
        ).all()

        results = []
        for user in users:
            if user.user_id in friend_ids:
                continue
            results.append(
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "nickname": user.nickname,
                }
            )

        return jsonify(results)
    finally:
        db.close()


@friends_bp.route("/send_friend_request", methods=["POST"])
def send_friend_request():
    if g.current_user is None:
        return jsonify({"error": "Not authenticated"}), 401

    db = Session()
    try:
        user_id = session["user_id"]
        target_id = request.form.get("user_id", type=int)
        target_username = (request.form.get("username") or "").strip()

        if target_id is None and not target_username:
            return jsonify({"error": "Missing target user"}), 400

        if target_id is None:
            user = db.query(User).filter(User.username == target_username).first()
            if user is None:
                return jsonify({"error": "User not found"}), 404
            target_id = user.user_id

        if target_id == user_id:
            return jsonify({"error": "Cannot add yourself"}), 400

        existing_friend = db.query(Friend).filter(
            ((Friend.user_id == user_id) & (Friend.friend_id == target_id))
            | ((Friend.user_id == target_id) & (Friend.friend_id == user_id))
        ).first()
        if existing_friend:
            return jsonify({"error": "Already friends"}), 400

        existing_request = db.query(FriendRequest).filter(
            ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == target_id))
            | ((FriendRequest.sender_id == target_id) & (FriendRequest.receiver_id == user_id)),
            FriendRequest.status == "pending",
        ).first()
        if existing_request:
            return jsonify({"error": "Request already pending"}), 400

        new_request = FriendRequest(
            sender_id=user_id,
            receiver_id=target_id,
            status="pending",
        )
        db.add(new_request)
        db.commit()

        return jsonify({"success": True})
    finally:
        db.close()


@friends_bp.route("/api/friends/on-campus", methods=["GET"])
def friends_on_campus():
    if g.current_user is None:
        return jsonify({"error": "Not authenticated"}), 401
    
    db = Session()

    try:
        today = date.today().isoformat()
        curr_time = datetime.now().strftime("%H:%M")

        user_id = g.current_user["user_id"]

        user_friends = get_friend_ids(db, user_id)

        if not user_friends:
            return jsonify({"on_campus": []})
        
        events = db.query(Event).filter(
            Event.user_id.in_(user_friends),
            Event.date == today,
            Event.start_time <= curr_time,
            Event.end_time >= curr_time
            ).all()
        
        if not events:
            return jsonify({"on_campus": []})
        
        friends_usernames = set()
        for e in events:
            friends_usernames.add(e.user_id)

        users = db.query(User).filter(User.user_id.in_(friends_usernames)).all()

        # Store the key value pair as user_id:username
        user_lookup = {}
        for u in users:
            user_lookup[u.user_id] = u

        results = []

        for e in events:
            u = user_lookup.get(e.user_id)

            if not u:
                continue
            results.append({
                "user_id" : u.user_id,
                "username" : u.username,
                "nickname" : u.nickname or u.username, # Store the username if nickname is empty
                "event_name" : e.event_name or "Untitled",
                "location" : e.location or "",
                "end_time" : e.end_time or ""
            })

        return jsonify({"on_campus": results})

    finally:
        db.close()