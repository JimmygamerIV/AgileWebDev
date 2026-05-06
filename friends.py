from flask import Blueprint, g, redirect, render_template, session
from database import Session
from models import User, Friend, FriendRequest
from forms import AddFriendForm, FriendActionForm

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

@friends_bp.route('/friends')
def friends():
    if g.current_user is None:
        return redirect('/signin')

    add_form = AddFriendForm()
    action_form = FriendActionForm()
    db = Session()
    try:
        user_id = session['user_id']

        # Get all friends for the user
        friend_ids = get_friend_ids(db, user_id)

        friends_list = db.query(User).filter(User.user_id.in_(friend_ids)).all()

        # Friend Requests
        r_rows = db.query(FriendRequest).filter(
            FriendRequest.receiver_id == user_id,
            FriendRequest.status == 'pending'
        ).all()

        sender_ids = []
        for i in r_rows:
            sender_ids.append(i.sender_id)
        
        senders = db.query(User).filter(User.user_id.in_(sender_ids)).all()

        requests = []
        for r in r_rows:
            for s in senders:
                # Check if user found 
                if s.user_id == r.sender_id:
                    requests.append({
                        "request_id": r.request_id,
                        "user_id": s.user_id,
                        "username": s.username
                    })
                    break
        
        return render_template(
            "friends.html",
            friends=friends_list,
            requests=requests,
            add_form = add_form,
            action_form = action_form,
            show_full_nav=True
        )
                
    finally:
        db.close()