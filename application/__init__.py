# -*- coding: utf-8 -*-
import eventlet
import logging
import pytz
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
    logging_level = app.config['LOGGING_LEVEL']
    logging_level_werkzeug = app.config['LOGGING_LEVEL_WERKZEUG']
    logging_level_socketio = app.config['LOGGING_LEVEL_SOCKETIO']
    logging_level_engineio = app.config['LOGGING_LEVEL_ENGINEIO']
    logging_level_handler = app.config['LOGGING_LEVEL_HANDLER']
    logging_max_bytes = app.config['LOGGING_MAX_BYTES']
    log_format = "%(asctime)s [%(levelname)s] %(message)s"

    logging.basicConfig(format=log_format, level=logging_level)

    # error log handler
    error_log_handler = RotatingFileHandler("application/log/error.log", maxBytes=logging_max_bytes, backupCount=1)
    error_log_handler.setLevel(logging_level_handler)
    error_log_handler.setFormatter(logging.Formatter(log_format))
    app.logger.addHandler(error_log_handler)

    # werkzeug logs
    logging.getLogger('werkzeug').setLevel(logging_level_werkzeug)
    logging.getLogger('werkzeug').addHandler(error_log_handler)

    # SocketIO logging
    logging.getLogger('socketio').setLevel(logging_level_socketio)
    logging.getLogger('engineio').setLevel(logging_level_engineio)
    logging.getLogger('socketio').addHandler(error_log_handler)
    logging.getLogger('engineio').addHandler(error_log_handler)


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