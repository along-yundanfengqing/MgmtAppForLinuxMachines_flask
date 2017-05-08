# -*- coding: utf-8 -*-
from wtforms import Form
from wtforms import StringField, PasswordField, BooleanField
from wtforms import validators


class LoginForm(Form):
    username = StringField('username', validators=[validators.DataRequired()])
    password = PasswordField('password', validators=[validators.DataRequired()])
    remember_me = BooleanField('remember_me')


class SignupForm(Form):
    username = StringField('username', validators=[validators.DataRequired()])
    password = PasswordField('password', validators=[validators.DataRequired(), validators.EqualTo('confirm', message='Password does not match.')])
    confirm = PasswordField('confirm_password', validators=[validators.DataRequired()])
