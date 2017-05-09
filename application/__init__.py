# -*- coding: utf-8 -*-
import eventlet
import logging
import pytz
import sys
from flask import Flask
app = Flask(__name__)
app.config.from_object('config')
from flask_socketio import SocketIO
socketio = SocketIO(app)
from logging.handlers import RotatingFileHandler

# my modules
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


def set_logging():
    logging_level_app = app.config['LOGGING_LEVEL_APPLICATION']
    logging_level_werkzeug = app.config['LOGGING_LEVEL_WERKZEUG']
    logging_level_socketio = app.config['LOGGING_LEVEL_SOCKETIO']
    logging_level_engineio = app.config['LOGGING_LEVEL_ENGINEIO']
    logging_level_to_file = app.config['LOGGING_LEVEL_TO_FILE']
    logging_max_bytes = app.config['LOGGING_MAX_BYTES']
    log_format = "%(asctime)s [%(levelname)s] %(message)s"

    logging.basicConfig(format=log_format, level=logging_level_app)

    if sys.version_info[0] == 3:
        # console log handler
        console_log_handler = logging.StreamHandler()
        console_log_handler.setFormatter(logging.Formatter(log_format))
        app.logger.addHandler(console_log_handler)

    # logging to a file
    file_handler = RotatingFileHandler("application/log/error.log", maxBytes=logging_max_bytes, backupCount=1)
    file_handler.setLevel(logging_level_to_file)
    file_handler.setFormatter(logging.Formatter(log_format))
    app.logger.addHandler(file_handler)

    # werkzeug logging
    logging.getLogger('werkzeug').setLevel(logging_level_werkzeug)
    logging.getLogger('werkzeug').addHandler(file_handler)

    # SocketIO logging
    logging.getLogger('socketio').setLevel(logging_level_socketio)
    logging.getLogger('engineio').setLevel(logging_level_engineio)
    logging.getLogger('socketio').addHandler(file_handler)
    logging.getLogger('engineio').addHandler(file_handler)


def start():
    print("Starting the program...\n")
    set_logging()
    app.register_blueprint(view)
    app.register_blueprint(api)
    eventlet.monkey_patch()
    app.jinja_env.filters['datetimefilter'] = datetimefilter
    app.jinja_env.filters['datetimefilter2'] = datetimefilter2

    DBManager()

    # Start background thread
    BackgroundThreadManager.start()


start()