from wtforms import Form
from wtforms import StringField, PasswordField, BooleanField
from wtforms import validators


class LoginForm(Form):
    username = StringField('Username', validators=[validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    remember_me = BooleanField('Remember me?')

class SignupForm(Form):
    username = StringField('Username', validators=[validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired(), validators.EqualTo('confirm', message='Password does not match.')])
    confirm = PasswordField('Confirm Password', validators=[validators.DataRequired()])
