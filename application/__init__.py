# -*- coding: utf-8 -*-
from flask import Flask
from application.modules.db_manager import DBManager


def create_app():
    my_app = Flask(__name__)
    my_app.config.from_object('config')
    my_mongo = DBManager(
        my_app.config['DATABASE_SERVER_IP'],
        my_app.config['DATABASE_NAME'],
        my_app.config['COLLECTION_NAME']
        )

    return my_app, my_mongo


# Create Flask app
app, mongo = create_app()

# Import controller
from application.modules import controllers
