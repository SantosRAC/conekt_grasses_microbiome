#!/usr/bin/env python3
import sys

# WSGI configuration
#
# WSGI_PATH = location of the app, should be the same as the base directory of the config file
# WSGI_ENV  = location of the activate_this.py script in the desired virtual environment
WSGI_PATH = '/home/jnov/Paged/conekt_grasses_microbiome/CoNekT_Grasses_Microbiome/conekt'
WSGI_ENV = '/home/jnov/Paged/conekt_grasses_microbiome/CoNekT_Grasses_Microbiome/bin/activate_this.py'


sys.path.insert(0, WSGI_PATH)

activator = WSGI_ENV
with open(activator) as f:
    exec(f.read(), {'__file__': activator})

# import the app. Note that it should not run by itself !
from conekt import create_app

application = create_app('config')