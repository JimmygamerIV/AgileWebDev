from flask import Blueprint, redirect, render_template, request, jsonify, abort, flash, url_for
from flask_login import login_required, current_user
from database import Session
from models import User, Friend, FriendRequest, Event
from forms import AddFriendForm, FriendActionForm
from datetime import date, datetime
from time_utils import get_now, get_today

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


def get_primary_poi_id(location_value):
        if not location_value:
                return None

        blocked_terms = {"online", "virtual", "remote", "zoom", "teams", "webex", "collaborate"}
        location_text = str(location_value).lower()
        if any(term in location_text for term in blocked_terms):
                return None

        for token in str(location_value).split("|"):
            poi_id = token.strip()
            if not poi_id:
                continue
            return poi_id

        return None


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
@login_required
def friends():
    """Display user's friends list and friend requests."""
    add_form = AddFriendForm()
    action_form = FriendActionForm()
    db = Session()
    try:
        user_id = current_user.user_id

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
                    "avatar": sender.avatar or "default.jpg",
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
                    "avatar": receiver.avatar or "default.jpg",
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
@login_required
def favourite_friend():
    db = Session()
    try:
        user_id = current_user.user_id
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
@login_required
def remove_friend():
    db = Session()
    try:
        user_id = current_user.user_id
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
        if 'application/json' in request.headers.get('Accept', ''):
            return jsonify({"success": True})
        return redirect(url_for('friends.friends'))
    finally:
        db.close()


@friends_bp.route("/accept_request", methods=["POST"])
@login_required
def accept_request():
    db = Session()
    try:
        user_id = current_user.user_id
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

        sender_user = db.query(User).filter(User.user_id == sender_id).first()

        db.commit()

        payload = {"success": True}
        if sender_user:
            payload["friend"] = {
                "user_id": sender_user.user_id,
                "username": sender_user.username,
                "nickname": sender_user.nickname,
                "avatar": sender_user.avatar or "default.jpg",
            }

        return jsonify(payload)
    finally:
        db.close()


@friends_bp.route("/reject_request", methods=["POST"])
@login_required
def reject_request():
    db = Session()
    try:
        user_id = current_user.user_id
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
@login_required
def cancel_request():
    db = Session()
    try:
        user_id = current_user.user_id
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
@login_required
def search_users():
    db = Session()
    try:
        user_id = current_user.user_id
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
                    "avatar": user.avatar or "default.jpg",
                }
            )

        return jsonify(results)
    finally:
        db.close()


@friends_bp.route("/send_friend_request", methods=["POST"])
@login_required
def send_friend_request():

    db = Session()
    try:
        user_id = current_user.user_id
        target_id = request.form.get("user_id", type=int)
        target_username = (request.form.get("username") or "").strip()

        if target_id is None and not target_username:
            return jsonify({"error": "Missing target user"}), 400

        target_user = None
        if target_id is None:
            target_user = db.query(User).filter(User.username == target_username).first()
            if target_user is None:
                return jsonify({"error": "User not found"}), 404
            target_id = target_user.user_id

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

        if target_user is None:
            target_user = db.query(User).filter(User.user_id == target_id).first()

        payload = {"success": True, "request_id": new_request.request_id}
        if target_user:
            payload["user"] = {
                "user_id": target_user.user_id,
                "username": target_user.username,
                "nickname": target_user.nickname,
                "avatar": target_user.avatar or "default.jpg",
            }
        return jsonify(payload)
    finally:
        db.close()


@friends_bp.route("/profile/<username>")
@login_required
def view_profile(username):
    
    db = Session()

    try:
        user = db.query(User).filter(User.username == username).first()

        if user is None:
            abort(404)

        is_self = user.user_id == current_user.user_id
        friend_ids = get_friend_ids(db, current_user.user_id)

        if not is_self and user.user_id not in friend_ids:
            return render_template(
                "not_friend.html",
                target_user=user,
                show_full_nav=True,
            ), 403

        status = "self" if is_self else "friend"
        incoming_req_id = None

        if status == "none":
            req = db.query(FriendRequest).filter(
                FriendRequest.sender_id == current_user.user_id,
                FriendRequest.receiver_id == user.user_id,
                FriendRequest.status == "pending" 
            ).first()

            if req:
                status = "sent_pending"


        # Check the friend req in the other direction
        if status == "none":
            req = db.query(FriendRequest).filter(
                FriendRequest.sender_id == user.user_id,
                FriendRequest.receiver_id == current_user.user_id,
                FriendRequest.status == "pending" 
            ).first()

            if req:
                status = "received_pending"
                incoming_req_id = req.request_id


        target_friend_ids = get_friend_ids(db, user.user_id)
        friend_count = len(target_friend_ids)
        mutual_count = 0 if is_self else len(friend_ids & target_friend_ids)

        today_str = get_today().isoformat()
        now_str = get_now().strftime("%H:%M")

        current_candidates = db.query(Event).filter(
            Event.user_id == user.user_id,
            Event.date == today_str,
            Event.start_time <= now_str,
            Event.end_time >= now_str,
        ).order_by(Event.start_time).all()

        current_class = next(
            (event for event in current_candidates if get_primary_poi_id(event.location or "")),
            None,
        )

        next_class = None
        if current_class is None:
            next_candidates = db.query(Event).filter(
                Event.user_id == user.user_id,
                ((Event.date > today_str) |
                ((Event.date == today_str) & (Event.start_time > now_str)))
            ).order_by(Event.date, Event.start_time).all()

            next_class = next(
                (event for event in next_candidates if get_primary_poi_id(event.location or "")),
                None,
            )

        return render_template(
            "user_profile.html",
            target_user=user,
            status=status,
            request_id=incoming_req_id,
            show_full_nav=True,
            friend_count=friend_count,
            mutual_count=mutual_count,
            current_class=current_class,
            next_class=next_class,
            on_campus=current_class is not None
        )
    
    finally:
        db.close()

    
@friends_bp.route("/api/friends/on-campus", methods=["GET"])
@login_required
def friends_on_campus():
    db = Session()

    try:
        today = get_today().isoformat()
        curr_time = get_now().strftime("%H:%M")

        user_id = current_user.user_id

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
