from flask import Flask, render_template, redirect, session
from database import init_db, Session
from models import Event
from auth import auth_bp
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = 'somesecretkey'

init_db()

app.register_blueprint(auth_bp)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/signin')
    
    db = Session()
    date_today = date.today()
    date_tomorrow = date_today + timedelta(days=1)


    # Fitler events by the date
    events = db.query(Event).filter(
        Event.user_id == session['user_id'],
        Event.date >= date_today.strftime("%Y-%m-%d"),
        #Event.date <= date_tomorrow.strftime("%Y-%m-%d")
    ).order_by(Event.date, Event.start_time).all()

    db.close()

    return render_template("index.html", events=events)

@app.route('/signin', methods=['GET'])
def signin():
    return render_template("signin.html")

@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

if __name__ == "__main__":
    app.run(debug=True)