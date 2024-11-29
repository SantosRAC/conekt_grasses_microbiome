# Setting up mod_wsgi with Apache

## Installing Apache2 and initial setup

Installing Apache2:

```bash
sudo apt install apache2
```

Common XXXXXX:

```bash
service apache2 status
service apache2 start # this could be used to start Apache2 if necessary (sudo may be necessary)
service apache2 stop # used to stop Apache2
```

Copy `conekt.template.wsgi` to conekt.wsgi and add the correct paths. 

    WSGI_PATH = 'location of your app' (e.g., `/path/to/CoNekT_Grasses_Microbiome`)
    WSGI_ENV = 'location of activate_this.py, in the bin folder of the virtual environment' (e.g., `/path/to/CoNekT_Grasses_Microbiome/bin/activate_this.py`)

`virtualenv` will automatically create the `activate_this.py` file inside the `/bin` folder.


The default apache2 user is called `www-data`.

A `.conf` file must be created in the sites-available (usually here: `/etc/apache2/sites-available/`).

VirtualHost

 * mods-available (wsgi.load loads the module from a particular environment - e.g., conekt_grasses)
 * mods-enabled (symbolic links to files in mods-available)

Configure apache, example below can be added to the default VirtualHost. A valid user (non-admin), usually www-data, is required for this:

    ServerName paged.unicamp.br
    ServerAlias www.paged.unicamp.br
    LogLevel debug
    #Include conf-available/serve-cgi-bin.conf

    # This part is optional, but will improve speed
    Alias /conekt/static /path/to/conekt/static

    <Directory /path/to/conekt/static>
        Require all granted
    </Directory>
	
	# Set up WSGI
	WSGIDaemonProcess application user=www-data group=www-data threads=5
	WSGIScriptAlias /conekt /path/to/conekt.wsgi

	<Location /conekt>
        WSGIProcessGroup application
	    WSGIApplicationGroup %{GLOBAL}
	    Require all granted
	</Location>

    ServerAdmin test_paged_unicamp@gmail.com
    DocumentRoot /path/to/conekt/static/
    ErrorLog /DataBig/apache_log/paged_error.log
    CustomLog /DataBig/apache_log/paged_access.log combined