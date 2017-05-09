# -*- coding: utf-8 -*-
import eventlet
import pytz
from flask import Flask
app = Flask(__name__)
app.config.from_object('config')
from flask_socketio import SocketIO
socketio = SocketIO(app)

# my modules
from application.modules import set_logging
from application.modules.api import api
from application.modules.bg_thread_manager import BackgroundThreadManager
from application.modules.db_manager import DBManager
from application.modules.machines_cache import MachinesCache
from application.modules.views import view


def datetimefilter(value, format="%B %d, %Y / %H:%M:%S"):
    tz = pytz.timezone('US/Pacific') # timezone you want to convert to from UTC
    utc = pytz.timezone('UTC')
    value = utc.localize(value, is_dst=None).astimezone(pytz.utc)
    local_dt = value.astimezone(tz)
    return local_dt.strftime(format)


def datetimefilter2(value, format="%Y%m%d_%H.%M.%S"):
    tz = pytz.timezone('US/Pacific') # timezone you want to convert to from UTC
    utc = pytz.timezone('UTC')
    value = utc.localize(value, is_dst=None).astimezone(pytz.utc)
    local_dt = value.astimezone(tz)
    return local_dt.strftime(format)


def start():
    print("Starting the program...\n")
    app.register_blueprint(view)
    app.register_blueprint(api)
    eventlet.monkey_patch()
    app.jinja_env.filters['datetimefilter'] = datetimefilter
    app.jinja_env.filters['datetimefilter2'] = datetimefilter2

    # Start background thread
    BackgroundThreadManager.start()


start()