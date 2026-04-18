from flask import Flask, render_template
from flask import request, redirect
from database import init_db
import sqlite3
import models

app = Flask(__name__)

init_db()


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/signin')
def signin():
    return render_template("signin.html")

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/friends')
def friends():
    conn = sqlite3.connect('unimap.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    user_id = 1  # TEMP

    # Get friends
    cursor.execute("""
        SELECT users.username, users.user_id
        FROM friends
        JOIN users ON friends.friend_id = users.user_id
        WHERE friends.user_id = ?
    """, (user_id,))
    friends_list = cursor.fetchall()

    # Get friend requests (incoming)
    cursor.execute("""
        SELECT friend_requests.request_id, users.username, users.user_id
        FROM friend_requests
        JOIN users ON friend_requests.sender_id = users.user_id
        WHERE friend_requests.receiver_id = ? AND status = 'pending'
    """, (user_id,))
    requests_list = cursor.fetchall()

    conn.close()

    return render_template(
        "Friends.html",
        friends=friends_list,
        requests=requests_list
    )

@app.route('/accept_request', methods=['POST'])
def accept_request():
    conn = sqlite3.connect('unimap.db')
    cursor = conn.cursor()

    request_id = request.form['request_id']
    sender_id = request.form['sender_id']
    user_id = 1  # TEMP

    # Mark request as accepted
    cursor.execute("""
        UPDATE friend_requests
        SET status = 'accepted'
        WHERE request_id = ?
    """, (request_id,))

    # Add both directions in friends table
    cursor.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", (user_id, sender_id))
    cursor.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", (sender_id, user_id))

    conn.commit()
    conn.close()

    return redirect('/friends?tab=requests')

@app.route('/reject_request', methods=['POST'])
def reject_request():
    conn = sqlite3.connect('unimap.db')
    cursor = conn.cursor()

    request_id = request.form['request_id']

    cursor.execute("""
        UPDATE friend_requests
        SET status = 'declined'
        WHERE request_id = ?
    """, (request_id,))

    conn.commit()
    conn.close()

    return redirect('/friends?tab=requests')

@app.route('/remove_friend', methods=['POST'])
def remove_friend():
    conn = sqlite3.connect('unimap.db')
    cursor = conn.cursor()

    friend_id = request.form['friend_id']
    user_id = 1  # TEMP

    cursor.execute("DELETE FROM friends WHERE user_id = ? AND friend_id = ?", (user_id, friend_id))
    cursor.execute("DELETE FROM friends WHERE user_id = ? AND friend_id = ?", (friend_id, user_id))

    conn.commit()
    conn.close()

    return redirect('/friends')

#Adds Test Users to Friends Page 
#Call using seed_test_data()
def seed_test_data():
    conn = sqlite3.connect('unimap.db')
    cursor = conn.cursor()

    # 🔴 Clear existing data (ORDER MATTERS because of foreign keys)
    cursor.execute("DELETE FROM friends")
    cursor.execute("DELETE FROM friend_requests")
    cursor.execute("DELETE FROM users")

    # 🟢 Insert fresh users
    cursor.execute("""
    INSERT INTO users (user_id, username, nickname, email, password_hash)
    VALUES (1, 'You', 'You', 'you@email.com', 'test123')
    """)

    cursor.execute("""
    INSERT INTO users (user_id, username, nickname, email, password_hash)
    VALUES (2, 'John Pork', 'John Pork', 'john@email.com', 'test123')
    """)

    # 🟢 Insert fresh friend request
    cursor.execute("""
    INSERT INTO friend_requests (request_id, sender_id, receiver_id, status)
    VALUES (1, 2, 1, 'pending')
    """)

    conn.commit()
    conn.close()

#Adds Test Users to Friends Page
seed_test_data()

if __name__ == "__main__":
    app.run(debug=True)