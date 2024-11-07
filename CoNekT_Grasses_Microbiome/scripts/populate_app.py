"""
Everything that needs to be set up to get flask running is initialized in this file.

  * set up and configure the app

  * configure the db

"""
from flask import Flask
from conekt.extensions import db

def create_app(populate_config):
    # Set up app and database

    app = Flask(__name__)

    with app.app_context():
    
        app.config.from_object(populate_config)
        configure_extensions(app)

        db.create_all()

    return app


def configure_extensions(app):
    db.app = app
    db.init_app(app)