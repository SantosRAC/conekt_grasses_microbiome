#!/usr/bin/env python3

import argparse
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import delete

# Create arguments
parser = argparse.ArgumentParser(description='Add clusters data to the database')
parser.add_argument('--cluster', type=int, metavar='cluster.txt',
                    dest='clusters_file',
                    help='The clusters information file',
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
    db_password = input('Enter the database password: ')

# Defining classes and functions


def add_cluster_from_file(clusters_file, empty = True):
    """Add clusters from a tabular file to the database.
    Returns the number of clusters added to the database.
    """

    # If required empty the table first
    file_size = os.stat(clusters_file).st_size
    if empty and file_size > 0:
        with engine.connect() as conn:
            stmt = delete(Cluster)
            conn.execute(stmt)
            conn.commit()

    cluster_count = 0

    # read the cluster file
    with open(clusters_file, 'r') as file:
        # get rid of the header
        _ = file.readline()

        lines = file.readlines()

        for line in lines:
            # split the line into the sample informatio
            parts = line.strip().split('\t')

            id = int(parts[0])
            gtdb_id = parts[1]

            # add the genoem to the database
            new_cluster = Cluster(id, gtdb_id)

            session.add(new_cluster)
            session.commit()

            cluster_count += 1

db_admin = args.db_admin
db_name = args.db_name

create_engine_string = "mysql+pymysql://"+db_admin+":"+db_password+"@localhost/"+db_name 

engine = create_engine(create_engine_string, echo=True)

# Reflect and existing database into a new model

Base = automap_base()

Base.prepare(engine, reflect=True)

Cluster = Base.classes.Cluster

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()
