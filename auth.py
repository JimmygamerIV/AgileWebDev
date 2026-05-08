from flask import Blueprint, g, request, render_template, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database import Session
from models import User
from forms import SignupForm, SigninForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.before_app_request
def load_current_user():
    g.current_user = None
    user_id = session.get("user_id")
    if not user_id:
        return

    db = Session()
    try:
        user = db.get(User, user_id)
        if user:
            g.current_user = {
                "user_id": user.user_id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email,
            }
        else:
            session.pop("user_id", None)
    finally:
        db.close()


# =========================
# SIGNUP
# =========================
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if request.method == 'GET':
        return render_template("signup.html", form=form, show_full_nav=False)

    if not form.validate_on_submit():
        return render_template("signup.html", form=form, show_full_nav=False)

    username = form.username.data
    nickname = form.nickname.data
    password = form.password.data
    confirm_password = form.confirm_password.data
    email = form.email.data.strip().lower() if form.email.data else None

    if ' ' in username:
        return render_template("signup.html", error="Username must not contain spaces.", form=form, show_full_nav=False)


    if password != confirm_password:
        return render_template("signup.html", error="Passwords do not match.", form=form, show_full_nav=False)
    
    if len(password) < 6:
        return render_template("signup.html", error="Password must be at least 6 characters long.", form=form, show_full_nav=False)
    
    if not re.search(r"[A-Z]", password):
        return render_template("signup.html", error="Password must contain at least one uppercase letter (A-Z).", form=form, show_full_nav=False)
    
    if not re.search(r"[a-z]", password):
        return render_template("signup.html", error="Password must contain at least one lowercase letter (a-z).", form=form, show_full_nav=False)
    
    if not re.search(r"\d", password):
        return render_template("signup.html", error="Password must contain at least one number (0-9).", form=form, show_full_nav=False)


    if not email:
        return render_template("signup.html", error="Email address cannot be empty.", form=form, show_full_nav=False)
    
    uwa_email_regex = r'^[a-zA-Z0-9._%+-]+@(student\.)?uwa\.edu\.au$'
    if not re.match(uwa_email_regex, email):
        return render_template("signup.html", error="Invalid domain. Please use a valid UWA email (@student.uwa.edu.au).", form=form, show_full_nav=False)


    hashed = generate_password_hash(password,method='pbkdf2:sha256')

    db = Session()
    try:
        existing_user = db.query(User).filter(User.username == username).first()
        existing_email = db.query(User).filter(User.email == email).first()

        if existing_user:
            return render_template("signup.html", error="User already exists", form=form, show_full_nav=False)

        if existing_email:
            return render_template("signup.html", error="Email is already registered", form=form, show_full_nav=False)

        new_user = User(
            username=username,
            nickname=nickname,
            email=email,
            password_hash=hashed
        )

        db.add(new_user)
        db.commit()

    except Exception as e:
        db.rollback()
        return render_template("signup.html", error=f"Registration failed: {e}", form=form, show_full_nav=False)
        
    finally:
        db.close()

    return redirect(url_for('auth.signin'))

# =========================
# SIGNIN
# =========================
@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SigninForm()

    if request.method == 'GET':
        return render_template("signin.html", form=form, show_full_nav=False)

    if not form.validate_on_submit():
        return render_template("signin.html", form=form, show_full_nav=False)

    username = form.username.data
    password = form.password.data

    db = Session()

    try:
        user = db.query(User).filter(User.username == username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.user_id
            return redirect(url_for('index'))

    finally:
        db.close()

    return render_template(
        "signin.html",
        error="The username or password you entered was incorrect",
        form=form,
        show_full_nav=False
    )


# ========================= 
# LOGOUT
# =========================
@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('auth.signin'))