Install apache and mod_wsgi for python 3.10, and the libmysql library:

    sudo apt-get install python3.10-dev libmysqlclient-dev apache2 apache2-dev libapache2-mod-wsgi-py3

# Creating the Flask configuration file

First, create a copy of the configuration template file. From the repo root, run:

```bash
cd CoNekT_Grasses_Microbiome/
cp config.template.py config.py
```

Change settings in `config.py`. **Apart from configuring paths, also change the secret key and the admin password !**


# Setting up MySQL/MariaDB for CoNekT Grasses Microbiome
 
In the config file the connection needs to be set up using :

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:pass@ip_address/database'
    
    
## Setting up the database using the MySQL CLI

First create a MySQL/MariaDB user with root:

    CREATE USER conekt_microbiome_admin@localhost IDENTIFIED BY 'E,~5*;{9f{p2VGp^';

The character set and collate are important as sqlalchemy-migrate doesn't work with utf8mb4 (the default).

    CREATE DATABASE conekt_microbiome_db CHARACTER SET latin1 COLLATE latin1_general_ci;

If the database already exists, change the character set as:

    ALTER DATABASE conekt_microbiome_db COLLATE = 'latin1_general_ci';
    
Give permissions to a user (conekt_microbiome_admin in this example) to access the database:

    GRANT INDEX, CREATE, DROP, SELECT, UPDATE, DELETE, ALTER, EXECUTE, INSERT on conekt_microbiome_db.* TO conekt_microbiome_admin@localhost;

    GRANT FILE on *.* TO conekt_microbiome_admin@localhost;


# Running the database migrations

Two commands are usually necessary, `initdb` (initialize the database) and `db init` (create a migration repository). From the repo root, run:

```bash
export FLASK_APP=run.py
cd CoNekT_Grasses_Microbiome/
flask initdb
flask db init
```


# Running the web application

```bash
flask run
```