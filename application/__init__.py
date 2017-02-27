# -*- coding: utf-8 -*-
import logging
from flask import Flask
app = Flask(__name__)
app.config.from_object('config')
from logging.handlers import RotatingFileHandler

# my modules
from application.modules.db_manager import DBManager


def set_logging():
    logging_level = app.config['LOGGING_LEVEL']
    logging_level_werkzeug = app.config['LOGGING_LEVEL_WERKZEUG']
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
    log_werkzeug = logging.getLogger('werkzeug')
    log_werkzeug.setLevel(logging_level_werkzeug)
    log_werkzeug.addHandler(error_log_handler)

# STARTING THE PROGRAM
print("Starting the program...\n")
set_logging()
mongo = DBManager(app)

from application.modules import controllers
