# -*- coding: utf-8 -*-
import logging
from flask import Flask
app = Flask(__name__)
app.config.from_object('config')
from application.modules.db_manager import DBManager


print("Starting the program...\n")
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

mongo = DBManager(app)

from application.modules import controllers
