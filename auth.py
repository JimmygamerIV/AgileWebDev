from flask import Blueprint, request, render_template, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database import Session
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template("signup.html", show_full_nav=False)

    username = request.form['username']
    nickname = request.form['nickname']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    email = request.form['email']

    if not username or not password:
        return render_template("signup.html",
                               error="Please fill in all required fields.",
                               show_full_nav=False)

    if ' ' in username:
        return render_template("signup.html",
                               error="Username must not contain spaces.",
                               show_full_nav=False)

    if password != confirm_password:
        return render_template("signup.html",
                               error="Passwords do not match.",
                               show_full_nav=False)

    hashed = generate_password_hash(password, method='pbkdf2:sha256')

    db = Session()
    existing_user = db.query(User).filter(User.username == username).first()
    existing_email = db.query(User).filter(User.email == email).first() if email else None

    if existing_user:
        db.close()
        return render_template("signup.html",
                               error="User already exists",
                               show_full_nav=False)

    if existing_email:
        db.close()
        return render_template("signup.html",
                               error="Email is already registered",
                               show_full_nav=False)

    new_user = User(
        username=username,
        nickname=nickname,
        email=email,
        password_hash=hashed
    )
    db.add(new_user)
    db.commit()
    db.close()

    return redirect(url_for('auth.signin'))


@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return render_template("signin.html", show_full_nav=False)

    username = request.form['username']
    password = request.form['password']

    db = Session()
    user = db.query(User).filter(User.username == username).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.user_id
        db.close()
        return redirect(url_for('index'))

    db.close()
    return render_template(
        "signin.html",
        error="The username or password you entered was incorrect",
        show_full_nav=False
    )


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('auth.signin'))