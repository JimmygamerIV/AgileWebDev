from flask_wtf import FlaskForm
from flask_wtf.file import FileField,FileAllowed,FileRequired
from wtforms import StringField, PasswordField,SubmitField,HiddenField
from wtforms.validators import DataRequired,EqualTo,Email,URL,Optional,Length

class SignupForm(FlaskForm):
    username = StringField("Username",validators = [DataRequired()])
    nickname = StringField("Nickname",validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password",validators=[DataRequired(),EqualTo("password")])
    email = StringField("Email",validators=[DataRequired(),Email()])
    submit = SubmitField("Sign Up")

class SigninForm(FlaskForm):
    username = StringField("username",validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Sign in")

class ImportTimetableForm(FlaskForm):
    ics_file =  FileField('Upload Your ICS Timetable File',validators = [Optional(),FileAllowed(['ics'],"Only Support .ics file! ")])
    ics_url = StringField('Your Personalised ICS file URL ',validators=[Optional(),URL(message="Please input valid URL" )])

    submit = SubmitField("Start Import")

class AddFriendForm(FlaskForm):
    target_username = StringField("Username",validators=[DataRequired(),Length(min=1,max=50)])
    submit = SubmitField("Send Friend Request")

class FriendActionForm(FlaskForm):
    request_id = HiddenField()
    accept = SubmitField("Accept")
    reject = SubmitField("Reject")
    
