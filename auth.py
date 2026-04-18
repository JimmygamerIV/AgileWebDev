from flask import Blueprint, request, render_template, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import Session
from models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])

def signup():
    if request.method == 'GET':
        return render_template("signup.html")

    username = request.form['username']
    nickname = request.form['nickname']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    email = request.form['email']

    if not username or not password or not email:
        return render_template("signup.html", error="Please fill in all required fields.")

    if ' ' in username:
        return render_template("signup.html", error="Username must not contain spaces.")

    if password != confirm_password:
        return render_template("signup.html", error="Passwords do not match.")
    
    hashed = generate_password_hash(password, method='pbkdf2:sha256')

    db = Session()
    existing_user = db.query(User).filter(User.username == username).first()
    existing_email = db.query(User).filter(User.email == email).first()

    # Check if user already exists or email is registered
    if existing_user:
        db.close()
        return render_template("signup.html", error="User already exists")
    if existing_email:
        db.close()
        return render_template("signup.html", error="Email is already registered")

    new_user = User(
        username=username,
        nickname=nickname,
        email=email,
        password_hash=hashed
    )
    db.add(new_user)
    db.commit()
    db.close()

    return redirect('/signin')

@auth_bp.route('/signin', methods=['GET', 'POST'])

def signin():
    if request.method == 'GET':
        return render_template("signin.html")

    username = request.form['username']
    password = request.form['password']

    db = Session()

    user = db.query(User).filter(User.username == username).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.user_id
        db.close()
        return redirect('/')
    
    db.close()
    return render_template("signin.html", error="The username or password you entered was incorrect")


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/signin')