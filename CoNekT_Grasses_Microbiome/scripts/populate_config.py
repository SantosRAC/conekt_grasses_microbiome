"""
Configuration of the website and database.

Copy this file to config.py and change the settings accordingly
"""
import os
import tempfile
basedir = os.getcwd()

SECRET_KEY = os.urandom(24)

# Database settings, database location and path to migration scripts
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://conekt_microbiome_admin:E,~5*;{9f{p2VGp^@localhost/conekt_microbiome_db'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'migration')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = DEBUG

# Debug settings
DEBUG_TB_INTERCEPT_REDIRECTS = False

# Customize link to Imprint and Privacy Policy(legal requirement in Germany)
IMPRINT_URL = None
PRIVACY_POLICY_URL = None