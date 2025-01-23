# Setting up mod_wsgi with Apache

Important: This configuration is for local development only and may have security vulnerabilities. It should not be used in a production environment.
Please refer to Apache documentation for hardening your web server.

## Installing Apache2 and initial setup

Installing Apache2:


```bash
sudo apt install apache2
```

Common Apache commands:

```bash
sudo service apache2 status       # Check the status of Apache2
sudo sudo service apache2 start   # this could be used to start Apache2 if necessary (sudo may be necessary)
sudo service apache2 stop         # used to stop 
sudo service apache2 reload       # used to reload Apache2
```

You may have to use:
```bash
sudo systemctl <command> apache2 #instead of "service"
```

Installing mod_wsgi for Python 3 that make the connection between Apache2 and wsgi:

```bash
sudo apt install libapache2-mod-wsgi-py3
```

Activate the module:
```bash
sudo a2enmod wsgi
sudo service apache2 restart
```
---

## Configuring the WSGI file

Copy `conekt.template.wsgi` to `conekt.wsgi` and replace the placeholders with the correct paths.

    WSGI_PATH = 'location of your app' (e.g., `/path/to/CoNekT_Grasses_Microbiome`)
    WSGI_ENV = 'location of activate_this.py, in the bin folder of the virtual environment' (e.g., `/path/to/CoNekT_Grasses_Microbiome/bin/activate_this.py`)

`virtualenv` will automatically create the `activate_this.py` file inside the `/bin` folder.

Example app.template.wsgi:
``` python

#!/usr/bin/env python3
import sys

# WSGI configuration
#
# WSGI_PATH = location of the app, should be the same as the base directory of the config file
# WSGI_ENV  = location of the activate_this.py script in the desired virtual environment

WSGI_PATH = 'location_of_your_app'  # e.g., /path/to/your_app
WSGI_ENV = 'path_to_activate_this.py'  # e.g., /path/to/venv/bin/activate_this.py

# Add the application path to the system path
sys.path.insert(0, WSGI_PATH)

# Activate the virtual environment
with open(WSGI_ENV) as f:
    exec(f.read(), {'_file_': WSGI_ENV})

# Import and initialize the Flask app
from your_app import create_app
application = create_app()

# Remenmber to replace:

# location_of_your_app with the directory containing your Flask app.

# path_to_activate_this.py with the path to activate_this.py in your virtual environment.

# your_app with the name of your Python module that contains the Flask app.

```

---

Apache configuration

A `.conf` file must be created in the sites-available (usually here: `/etc/apache2/sites-available/`).

1. Create a .conf file in /etc/apache2/sites-available/. For example:

```bash
sudo nano /etc/apache2/sites-available/your_app.conf
```
2. Example your_app.conf:

```
<VirtualHost *:80>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com

    # Static files configuration
    # This part is optional, but will improve speed
    Alias /conekt/static /path/to/conekt/static

    <Directory /path/to/your_app/static>
        Require all granted
        Allow from all
    </Directory>

    # WSGI configuration
    WSGIDaemonProcess your_app user=www-data group=www-data threads=5 python-path=/path/to/your_app python-home=/path/to/venv
    WSGIProcessGroup your_app
    WSGIScriptAlias / /path/to/your_app/app.wsgi

    <Directory /path/to/your_app>
        <Files app.wsgi>
            Require all granted
            Allow from all
        </Files>
    </Directory>

    ServerAdmin your_email@domain.com
    # DocumentRoot for your application
    DocumentRoot /path/to/your_app

    # Log files
    LogLevel debug
    ErrorLog /Directory/apache_log/paged_error.log
    CustomLog /Directory/apache_log/paged_access.log combined

</VirtualHost>
```

Replace:

/path/to/your_app with the directory of your Flask application.

/path/to/venv with the path to your virtual environment.


The default apache2 user is called `www-data`. Please ensure that it has complete access to your app content.

3. Enable the site and reload Apache:

```bash
sudo a2ensite your_app.conf
sudo systemctl reload apache2
```

---

### Testing the setup

Access your application at http://yourdomain.com. If there are issues, check Apache's error logs:

```bash
sudo tail -f /Directory/apache_log/paged_error.log
```

---
