import logging
import sys
from logging.handlers import RotatingFileHandler

from application import app

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

set_logging()