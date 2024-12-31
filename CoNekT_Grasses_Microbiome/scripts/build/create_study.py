#!/usr/bin/env python3

import argparse

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from collections import defaultdict

from tempfile import mkstemp
import os

parser = argparse.ArgumentParser(description='Create a study and add to the database')
parser.add_argument('--species_code', type=str, metavar='Zma',
                    dest='species_code',
                    help='The CoNekT Microbiome species code',
                    required=True)
parser.add_argument('--study_name', type=str, metavar='Integration of Maize Microbiome and Transcriptome in leaves',
                    dest='study_name',
                    help='A name for the study',
                    required=True)
parser.add_argument('--study_description', type=str, metavar='Integration of Maize Microbiome and Transcriptome in leaves to understand the role of microbiome in plant transcriptome',
                    dest='study_description',
                    help='A description for the study',
                    required=True)
parser.add_argument('--study_type', type=str, metavar='expression_metataxonomics',
                    dest='study_type',
                    help='Study type',
                    required=True)
parser.add_argument('--krona_file', type=str, metavar='krona.html',
                    dest='krona_file',
                    help='Krona file',
                    required=True)
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


def build_study(species_code, study_name, study_description,
                    study_type, krona_file):
    
    # Check if species exists in the database
    with engine.connect() as conn:
        stmt = select(Species).where(Species.__table__.c.code == species_code)
        species = conn.execute(stmt).first()

    if not species:
        print(f"Species ({species_code}) not found in the database.")
        exit(1)
    else:
        species_id = species.id

    krona_file_content = open(krona_file, 'r').read()

    new_study = {"name": study_name,
                 "description": study_description,
                "data_type": study_type,
                "species_id": species_id,
                "krona_html": krona_file_content}

    session.add(Study(**new_study))
    session.commit()


sps_code = args.species_code
study_name = args.study_name
study_description = args.study_description
study_type = args.study_type
krona_file = args.krona_file
db_admin = args.db_admin
db_name = args.db_name

create_engine_string = "mysql+pymysql://"+db_admin+":"+db_password+"@localhost/"+db_name

engine = create_engine(create_engine_string, echo=True)

# Reflect an existing database into a new model
Base = automap_base()

Base.prepare(engine, reflect=True)

Species = Base.classes.species
Study = Base.classes.studies

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()

# Run function to create a study and add it to the database
build_study(sps_code, study_name, study_description,
                    study_type, krona_file)

session.close()

