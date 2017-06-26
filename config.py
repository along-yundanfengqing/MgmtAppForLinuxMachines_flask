import logging

# Application
DEBUG = False
TESTING = False
JSON_SORT_KEYS = False
SECRET_KEY = "super_secret_key"
APPLICATION_HOST = "127.0.0.1"
APPLICATION_PORT = 5000
BG_THREAD_TIMER = 30        # Seconds
LOGIN_FILENAME = "login.txt"

# Logging
LOGGING_LEVEL_APPLICATION = logging.INFO            #  DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGGING_LEVEL_WERKZEUG = logging.ERROR  #  DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGGING_LEVEL_TO_FILE = logging.ERROR   #  DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGGING_LEVEL_SOCKETIO = logging.ERROR   #  DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGGING_LEVEL_ENGINEIO = logging.ERROR   #  DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGGING_MAX_BYTES = 1000000

# MongoDB
MONGO_DATABASE_HOST = "172.30.0.99"
MONGO_DATABASE_PORT = 27017
MONGO_DATABASE_NAME = "LinuxMachines"
MONGO_COLLECTION_NAME = "machines"