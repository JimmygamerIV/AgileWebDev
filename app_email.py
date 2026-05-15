from flask_mail import Mail,Message
from threading import Thread
from flask import current_app
import random
import string


mail = Mail()

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_welcome_email(recipient_email,nickname):
    msg = Message(
        subject = "Welcome to UWA Social Timetable!.",
        recipients=[recipient_email]
    )
    msg.body = f"Hi {nickname},\n\nWelcome to Unimap! Your account has been created"

    app = current_app._get_current_object()
    Thread(target=send_async_email, args=(app, msg)).start()

def send_verification_code(recipient_email):
    code = "".join(random.choices(string.digits,k=6))

    msg = Message(
        subject = f"Your Verification Code is: {code}",
        recipients = [recipient_email]
    )
    msg.body = f"Your verification code is : {code}."

    try:
        app = current_app._get_current_object()
        Thread(target=send_async_email,args=(app,msg)).start()
        return code
    except Exception as e:
        print(f"Mail Error: {e}")
        return None