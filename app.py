from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
from datetime import timedelta

basedir = os.path.dirname(__file__)
db_path = os.path.join(basedir, "database", "unimap.db")
app = Flask(__name__)

# --- Configuration ---
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# REQUIRED: Secret key is used to cryptographically sign the session cookie
app.secret_key = 'dev_key_123456' 

# Optional: Set session expiration (e.g., 7 days)
app.permanent_session_lifetime = timedelta(days=7)

db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    nickname = db.Column(db.Text)
    email = db.Column(db.Text, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    timetable_link = db.Column(db.Text)

# --- Routes ---

@app.route('/signup', methods=["GET","POST"])
def signup():
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        nick = request.form.get("nickname", "").strip()
        email = request.form.get("email", "").strip() if request.form.get("email") else None
        pword = request.form.get("password", "")
        confirm_pword = request.form.get("confirm_password","")

        # Validation: Username length
        if not uname or len(uname) < 4:
            return jsonify({"status": "error", "message": "Username must be 4+ chars"}), 400

        # Validation: Password security (at least 1 upper, 1 lower, 1 special char, 8+ total)
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[^\w\s]).{8,}$'
        if not re.match(password_regex, pword):
            return jsonify({"status": "error", "message": "Password security requirements not met"}), 400

        # Validation: Password confirmation
        if pword != confirm_pword:
            return jsonify({"status":"error","message":"Passwords do not match."}), 400
            
        # Validation: Check if username exists
        if User.query.filter_by(username=uname).first():
            return jsonify({"status": "error", "message": "Username already exists"}), 400
        
        # Validation: Check if email exists (if provided)
        if email and User.query.filter_by(email=email).first():
            return jsonify({"status": "error", "message": "Email already registered"}), 400
        
        try:
            new_user = User(
                username=uname,
                nickname=nick if nick else uname,
                email=email,
                password_hash=generate_password_hash(pword)
            )
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"status": "success", "message": "Account created successfully"}), 200
        except Exception as e:
            db.session.rollback()
            print(f"Signup error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500
            
    return render_template("signup.html")

@app.route('/')
@app.route("/signin", methods=["GET","POST"])
def signin_page():
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        pword = request.form.get("password", "")

        user = User.query.filter_by(username=uname).first()

        # Verify user existence and password hash
        if user and check_password_hash(user.password_hash, pword):
            # Store user info in session upon successful login
            session.permanent = True  # Enable the lifetime set in config
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['nickname'] = user.nickname if user.nickname else user.username
            session['email'] = user.email if user.email else ''
            
            return jsonify({
                "status": "success", 
                "message": "Login successful!",
                "redirect": url_for('homepage')
            }), 200
        else:
            return jsonify({"status": "error", "message": "Invalid username or password"}), 401
    
    return render_template("signin.html")

@app.route('/homepage')
def homepage():
    # Authentication Check: If user_id not in session, redirect to login
    if 'user_id' not in session:
        return redirect(url_for('signin_page'))
    
    # Verify user still exists in database
    user = User.query.get(session.get('user_id'))
    if not user:
        session.clear()
        return redirect(url_for('signin_page'))
    
    # Pass session data to the template
    return render_template("index.html", 
                         username=session.get('username'),
                         nickname=session.get('nickname'),
                         email=session.get('email'))

@app.route('/logout')
def logout():
    # Clear all data from the session
    session.clear()
    return redirect(url_for('signin_page'))

# --- Database Initialization ---
def init_db():
    """Initialize database tables"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully")

if __name__ == '__main__':
    # Initialize database on first run
    init_db()
    app.run(debug=True)