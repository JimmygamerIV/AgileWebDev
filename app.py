from flask import Flask, render_template
from database import init_db
import models

app = Flask(__name__)

init_db()

@app.route('/')
def index():
    return render_template("Main.html")

@app.route('/signin')
def signin():
    return render_template("Signin.html")

@app.route('/signup')
def signup():
    return render_template('Signup.html')

if __name__ == "__main__":
    app.run(debug=True)