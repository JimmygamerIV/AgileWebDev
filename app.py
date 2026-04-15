from flask import Flask, render_template
from database import init_db
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

if __name__ == "__main__":
    app.run(debug=True)