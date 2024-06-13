#!/usr/bin/env python3

import argparse
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import delete

# TODO: include SILVA taxonomy

# Create arguments
parser = argparse.ArgumentParser(description='Add taxonomy data to the database')
parser.add_argument('--ncbi_nodes', type=str, metavar='nodes.dmp',
                    dest='ncbi_nodes_file',
                    help='The nodes file from NCBI taxonomy',
                    required=False)
parser.add_argument('--ncbi_names', type=str, metavar='names.dmp',
                    dest='ncbi_nodes_file',
                    help='The nodes file from NCBI taxonomy',
                    required=False)
parser.add_argument('--db_admin', type=str, metavar='DB admin',
                    dest='db_admin',
                    help='The database admin user',
                    required=True)
parser.add_argument('--db_name', type=str, metavar='DB name',
                    dest='db_name',
                    help='The database name',
                    required=True)
parser.add_argument('--db_password', type=str, metavar='DB password',
                    dest='db_password',
                    help='The database password',
                    required=False)

args = parser.parse_args()

if args.db_password:
    db_password = args.db_password
else:
    db_password = input("Enter the database password: ")

#TODO: function to add taxonomy data to the database

db_admin = args.db_admin
db_name = args.db_name

create_engine_string = "mysql+pymysql://"+db_admin+":"+db_password+"@localhost/"+db_name

engine = create_engine(create_engine_string, echo=True)

# Reflect an existing database into a new model
Base = automap_base()

Base.prepare(engine, reflect=True)

NCBITaxon = Base.classes.ncbi_taxonomy

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()

ncbi_nodes_file = args.ncbi_nodes_file
ncbi_names_file = args.ncbi_names_file




session.close()