import re
from flask import Blueprint, request, render_template, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from database import Session
from models import User
from forms import SignupForm, SigninForm
from app_email import send_welcome_email, send_verification_code
from auth_utils import validate_password, validate_uwa_email

# Flask-Login core methods
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint("auth", __name__)

# =========================
# SIGNUP
# =========================
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration route.
    
    Validates:
        - Username uniqueness and format (no spaces)
        - Password strength (6+ chars, uppercase, lowercase, digit)
        - Password confirmation match
        - Email validity (UWA domain only)
        - Email uniqueness
    
    On successful registration, user is auto-logged in.
    """
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

    # Validate username format
    if ' ' in username:
        error = "Username must not contain spaces."
        return render_template("signup.html", error=error, form=form, show_full_nav=False)

    # Validate password match
    if password != confirm_password:
        error = "Passwords do not match."
        return render_template("signup.html", error=error, form=form, show_full_nav=False)
    
    # Validate password strength using utility function
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return render_template("signup.html", error=error_msg, form=form, show_full_nav=False)

    # Validate email using utility function
    is_valid, error_msg = validate_uwa_email(email)
    if not is_valid:
        return render_template("signup.html", error=error_msg, form=form, show_full_nav=False)

    hashed = generate_password_hash(password, method='pbkdf2:sha256')

    db = Session()
    try:
        existing_user = db.query(User).filter(User.username == username).first()
        existing_email = db.query(User).filter(User.email == email).first()

        if existing_user:
            error = "Username already exists. Please choose another one."
            return render_template("signup.html", error=error, form=form, show_full_nav=False)

        if existing_email:
            error = "Email is already registered. Try signing in or resetting your password."
            return render_template("signup.html", error=error, form=form, show_full_nav=False)

        new_user = User(
            username=username,
            nickname=nickname,
            email=email,
            password_hash=hashed
        )

        db.add(new_user)
        db.commit()
        
        # Auto-login new user after signup
        login_user(new_user, remember=False)
        flash('Account created successfully! Welcome aboard!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.rollback()
        error = f"Registration failed: {str(e)}"
        return render_template("signup.html", error=error, form=form, show_full_nav=False)
    finally:
        db.close()


# =========================
# SIGNIN
# =========================
@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    """User login route with "Remember Me" functionality.
    
    GET: Display signin form
    POST: Process login credentials and establish session
    """
    form = SigninForm()

    if request.method == 'GET':
        return render_template(
            "signin.html",
            form=form,
            reset_success=request.args.get("reset") == "1",
            show_full_nav=False
        )

    if not form.validate_on_submit():
        return render_template("signin.html", form=form, show_full_nav=False)

    username = form.username.data
    password = form.password.data
    remember_me = form.remember_me.data  # Get "Remember Me" checkbox value

    db = Session()
    try:
        user = db.query(User).filter(User.username == username).first()

        if user and check_password_hash(user.password_hash, password):
            # Login user with remember_me option
            # If remember_me is True, session expires in 30 days
            # Otherwise, session expires when browser closes
            login_user(user, remember=remember_me)
            
            # Redirect to next page or index
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
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
@login_required
def logout():
    """Logout route that clears user session.
    
    Requires POST method for security (prevents CSRF).
    Only accessible to authenticated users.
    """
    username = current_user.username
    logout_user()
    flash(f'Goodbye, {username}! You have been logged out.', 'success')
    return redirect(url_for('auth.signin'))


# =========================
# FORGOT PASSWORD & RESET PASSWORD
# =========================
@auth_bp.route('/forgot_password', methods=['GET', "POST"])
def forgot_password():
    """Password reset request route.
    
    GET: Display email input form
    POST: Send verification code to email
    """
    if request.method == 'GET':
        return render_template('forgot_password.html', show_full_nav=False)
    
    email = request.form.get('email', '').strip().lower()
    
    # Validate email format
    is_valid, error_msg = validate_uwa_email(email)
    if not is_valid:
        return render_template("forgot_password.html", error=error_msg, show_full_nav=False)

    db = Session()
    try:
        user = db.query(User).filter(User.email == email).first()
        session['reset_email'] = email
        session.pop('reset_code', None)

        if user:
            code = send_verification_code(email)
            if code:
                session['reset_code'] = code
                flash('Verification code sent to your email.', 'info')
        else:
            # Don't reveal if email exists (security best practice)
            flash('If an account with this email exists, a verification code will be sent.', 'info')

        return redirect(url_for("auth.reset_password"))
    finally:
        db.close()


@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """Password reset confirmation route.
    
    GET: Display verification code and new password form
    POST: Verify code and update password
    """
    if 'reset_email' not in session:
        flash('Please start by requesting a password reset.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'GET':
        return render_template("reset_password.html", email=session['reset_email'], show_full_nav=False)

    user_code = request.form.get('code', '')
    new_password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    # Verify code
    if user_code != session.get('reset_code'):
        error = "Invalid verification code. Please try again."
        return render_template("reset_password.html", error=error, show_full_nav=False)

    # Verify passwords match
    if new_password != confirm_password:
        error = "Passwords do not match."
        return render_template("reset_password.html", error=error, show_full_nav=False)

    # Validate password strength
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return render_template("reset_password.html", error=error_msg, show_full_nav=False)

    db = Session()
    try:
        user = db.query(User).filter(User.email == session['reset_email']).first()
        if user:
            user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
            db.commit()
            
            session.pop('reset_email', None)
            session.pop('reset_code', None)
            
            flash('Password reset successful! Please sign in with your new password.', 'success')
            return redirect(url_for('auth.signin'))
        else:
            error = "User not found. Please start over."
            return render_template("reset_password.html", error=error, show_full_nav=False)
    except Exception as e:
        db.rollback()
        error = f"Database error: {str(e)}"
        return render_template("reset_password.html", error=error, show_full_nav=False)
    finally:
        db.close()