#!/usr/bin/env python3

import argparse
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import delete

# Create arguments
parser = argparse.ArgumentParser(description='Add ontology data to the database')
parser.add_argument('--envo', type=str, metavar='envo.txt',
                    dest='envo_file',
                    help='The environment ontology file',
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


def add_tabular_envo(filename, empty=True):

    # If required empty the table first
    file_size = os.stat(filename).st_size
    if empty and file_size > 0:
        # If required empty the table first
        with engine.connect() as conn:
            stmt = delete(EnvironmentOntology)
            conn.execute(stmt)
            conn.commit()

    with open(filename, 'r') as file:
        # get rid of the header
        _ = file.readline()

        lines = file.readlines()

        for line in lines:
            #split the line into the ENVO informations
            parts = line.strip().split('\t')
            envo_term = parts[0]
            envo_name = parts[1]
            envo_annotation = parts[2]

            envo_ontology = EnvironmentOntology(envo_term, envo_name, envo_annotation)
            session.add(envo_ontology) 
            session.commit() 
         
            session.commit()

db_admin = args.db_admin
db_name = args.db_name

create_engine_string = "mysql+pymysql://"+db_admin+":"+db_password+"@localhost/"+db_name

engine = create_engine(create_engine_string, echo=True)

# Reflect an existing database into a new model
Base = automap_base()

Base.prepare(engine, reflect=True)

EnvironmentOntology = Base.classes.environment_ontology

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()

envo_file = args.envo_file

ontology_data_count = 0

if envo_file:
    ontology_data_count+=1
    add_tabular_envo(envo_file)

if ontology_data_count == 0:
    print("Must add at least one type of ontology data (e.g., --plant_ontology)\
          to the database!")
    exit(1)

session.close()