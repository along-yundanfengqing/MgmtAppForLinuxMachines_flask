# -*- coding: utf-8 -*-
import eventlet
eventlet.monkey_patch()
import pytz
from flask_socketio import SocketIO

# my modules
from application.factory import create_app

app = create_app()
socketio = SocketIO(app)

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
    from application.views import view
    from application.api import api
    app.register_blueprint(view)
    app.register_blueprint(api)
    app.jinja_env.filters['datetimefilter'] = datetimefilter
    app.jinja_env.filters['datetimefilter2'] = datetimefilter2

    from application.modules.set_logging import set_logging
    from application.modules.db_manager import DBManager
    from application.modules.machines_cache import MachinesCache




start()