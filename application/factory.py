import pytz
from flask import Flask

def create_app(config=None):
    app = Flask(__name__)

    app.config.from_object('config')

    return app
