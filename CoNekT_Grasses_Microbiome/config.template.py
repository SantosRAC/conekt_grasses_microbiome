"""
Configuration of the website and database.

Copy this file to config.py and change the settings accordingly
"""
import os
import tempfile
basedir = os.getcwd()

# Flask settings, make sure to turn DEBUG and TESTING to False for production
DEBUG = True
TESTING = True

SECRET_KEY = os.urandom(24)

# Login settings + admin account
LOGIN_ENABLED = True

# Credentials for admin account
# Remove this after creating the database !
ADMIN_PASSWORD = 'admin'
ADMIN_EMAIL = 'admin@web.com'

# Database settings, database location and path to migration scripts
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://conekt_microbiome_admin:E,~5*;{9f{p2VGp^@localhost/conekt_microbiome_db'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'migration')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = DEBUG

# Settings for the FTP/bulk data
PLANET_FTP_DATA = os.path.join(basedir, 'ftp')

# Settings for Cache
CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 120
CACHE_THRESHOLD = 10000

WTF_CSRF_TIME_LIMIT = None

# Minify pages when debug is off
MINIFY_PAGE = not DEBUG

# Solr settings
TODO: add Solr settings

# temp dir
TMP_DIR = tempfile.mkdtemp()

# BLAST settings
BLAST_ENABLED = False
BLAST_TMP_DIR = tempfile.mkdtemp()
BLASTP_PATH = ''
BLASTP_DB_PATH = ''
BLASTN_PATH = ''
BLASTN_DB_PATH = ''
BLASTP_CMD = '"' + BLASTP_PATH + '" -db "' + BLASTP_DB_PATH + '" -query "<IN>" -out "<OUT>" -outfmt 6 -num_threads 1'
BLASTN_CMD = '"' + BLASTN_PATH + '" -db "' + BLASTN_DB_PATH + '" -query "<IN>" -out "<OUT>" -outfmt 6 -num_threads 1'

MAKEBLASTDB_PATH = ''
MAKEBLASTDB_PROT_CMD = '"' + MAKEBLASTDB_PATH + '" -in "<IN>"' ' -out "' + BLASTP_DB_PATH + '" -dbtype prot'
MAKEBLASTDB_NUCL_CMD = '"' + MAKEBLASTDB_PATH + '" -in "<IN>"' ' -out "' + BLASTN_DB_PATH + '" -dbtype nucl'


# Debug settings
DEBUG_TB_INTERCEPT_REDIRECTS = False

# Front Page Options
# Twitter handle (None to disable twitter feed)
TWITTER_HANDLE = None
KEYWORD_EXAMPLES = []

# Global message
# This message will be injected on each page !
# Can be used to announce maintenance, ...
GLOB_MSG = None
GLOB_MSG_TITLE = 'Info'

# Tutorial URL
TUTORIAL_URL = "" #TODO: add tutorial URL (LabBCES)

# Customize link to Imprint and Privacy Policy(legal requirement in Germany)
IMPRINT_URL = None
PRIVACY_POLICY_URL = None