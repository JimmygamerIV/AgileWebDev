from flask import Flask, render_template, redirect, session
from database import init_db, Session
from models import Event
from auth import auth_bp
from datetime import date, timedelta, datetime

app = Flask(__name__)
app.secret_key = 'somesecretkey'

init_db()

app.register_blueprint(auth_bp)


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/signin')
    
    db = Session()
    try:
        all_events = db.query(Event).filter(Event.user_id == session['user_id']).order_by(Event.date, Event.start_time).all()
        events = []

        today = date.today()
        tomorrow = today + timedelta(days=1)
        time_now = datetime.now().strftime("%H:%M")

        # Add today's and tommorow's classes to the array
        for e in all_events:
            if not e.date:
                continue
            event_date = date.fromisoformat(e.date)

            if event_date == today and e.start_time >= time_now:
                events.append(e)

            elif event_date == tomorrow:
                events.append(e)
        
        # If there are no upcomming classes for the two days then add next furutre upcoming
        if not events:
            for e in all_events:
                if not e.date:
                    continue

                event_date = date.fromisoformat(e.date)
                if event_date > tomorrow:
                    events.append(e)

                # Only add the next 2 upcoming events
                if len(events) == 2:
                    break
                
    finally:
        db.close()

    return render_template("index.html", events=events)

if __name__ == "__main__":
    app.run(debug=True)