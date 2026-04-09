from flask import Flask, render_template, request, redirect,url_for,jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
import os
import re


basedir = os.path.dirname(__file__)
db_path = os.path.join(basedir,"database","unimap.db")
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"
    

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    nickname = db.Column(db.Text)
    

    password_hash = db.Column(db.Text, nullable=False)
    
    timetable_link = db.Column(db.Text)


@app.route('/')
@app.route('/signup', methods=["GET","POST"])
def signup():
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        nick = request.form.get("nickname", "").strip()
        pword = request.form.get("password", "")
        confirm_pword = request.form.get("confirm_password","")

        # Validation: Username
        if not uname or len(uname) < 4:
            return jsonify({"status": "error", "message": "Username must be 4+ chars"}), 400

        # Validation: Password (Regex)
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[^\w\s]).{8,}$'
        if not re.match(password_regex, pword):
            return jsonify({"status": "error", "message": "Password security requirements not met"}), 400

        if pword != confirm_pword:
            return jsonify({"status":"error","message":"Passwords do not match. Please try again."}),400
        # Validation: Database Uniqueness
        if User.query.filter_by(username=uname).first():
            return jsonify({"status": "error", "message": "Username already exists"}), 400

        
        try:
            new_user = User(
                username=uname,
                nickname=nick if nick else None,
                password_hash=generate_password_hash(pword)
            )
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"status": "success", "message": "Account created successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Internal server error"}), 500
    return render_template("Signup.html")


@app.route("/signin",methods=["GET","POST"])
def signin_page():
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        pword = request.form.get("password", "")

       
        user = User.query.filter_by(username=uname).first()

        if user and check_password_hash(user.password_hash, pword):
            return jsonify({
                "status": "success", 
                "message": "Login successful! Redirecting...",
                "redirect": url_for('homepage')
            }), 200
        else:

            return jsonify({"status": "error", "message": "Invalid username or password"}), 401
    
    return render_template("Signin.html")

@app.route('/homepage')
def homepage():
   
    return render_template("homepage.html")

@app.route('/test_db')
def test_db():
    try:
        if not os.path.exists(db_path):
            return f"Error!"
        
        first_user = User.query.first()
        if first_user:
            return f"Success!"
        return "Success! "
    except Exception as e:
        return f"Error: {str(e)}"
    
if __name__ == '__main__':
    app.run(debug=True)