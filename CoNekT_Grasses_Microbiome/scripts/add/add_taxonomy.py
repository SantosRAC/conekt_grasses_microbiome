#!/usr/bin/env python3

import argparse
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import delete

# Create arguments
parser = argparse.ArgumentParser(description='Add taxonomy data to the database')
parser.add_argument('--silva_taxonomy_file', type=str, metavar='tax_slv_lsu_138.1.txt',
                    dest='silva_taxonomy_file',
                    help='The SILVA taxonomy',
                    required=False)
parser.add_argument('--silva_release', type=str, metavar='138.1',
                    dest='silva_release',
                    help='SILVA taxonomy release number.',
                    required=False)
parser.add_argument('--gg_taxonomy_file', type=str, metavar='',
                    dest='gg_taxonomy_file',
                    help='The GreenGenes taxonomy',
                    required=False)
parser.add_argument('--gg_release', type=str, metavar='',
                    dest='gg_release',
                    help='GreenGenes taxonomy release number.',
                    required=False)
parser.add_argument('--gtdb_taxonomy_file', type=str, metavar='',
                    dest='gtdb_taxonomy_file',
                    help='The GTDB taxonomy',
                    required=False)
parser.add_argument('--gtdb_release', type=str, metavar='',
                    dest='gtdb_release',
                    help='GTDB taxonomy release number.',
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

# Defining classes and functions

def add_silva_taxonomy(silva_taxonomy_data, silva_release, empty=True):
    """
    Adds SILVA taxonomy information to the database.

    :param taxonomy_data: SILVA taxonomy data (e.g., tax_slv_ssu_138.txt)
    :param release: SILVA release number (e.g., 138)
    #TODO: store release number in the database
    :param empty: Empty the database first when true (default: True)
    :return: 
    """

    # If required empty the table first
    if empty:
        with engine.connect() as conn:
            stmt = delete(SILVATaxon)
            conn.execute(stmt)

    new_taxons = []
    taxon_count = 0

    # read the taxonomy file
    with open(silva_taxonomy_data, 'r') as file:
        lines = file.readlines()

        for line in lines:

            # split the line into the taxonomy information
            # Columns 4 and 5 are not used (remark and release)
            line = line.strip().split('\t')

            # add the taxonomy information to the database
            new_taxon = SILVATaxon(**{"taxon_path": line[0],
                                        "ncbi_taxid": line[1],
                                        "rank": line[2]})

            session.add(new_taxon)
            new_taxons.append(new_taxon)
            taxon_count += 1

        # add 400 taxons at the time, more can cause problems with some database engines
        if len(new_taxons) > 400:
            session.commit()
            new_taxons = []

    # add the last set of sequences
    session.commit()

    return taxon_count

def add_gg_taxonomy(gg_taxonomy_data, gg_release, empty=True):
    """
    Adds GreenGenes taxonomy information to the database.

    :param taxonomy_data: GG taxonomy data (e.g., gg_13_5_taxonomy.txt)
    :param release: GreenGenes release number (e.g., 13.5)
    #TODO: store release number in the database
    :param empty: Empty the database first when true (default: True)
    :return: 
    """
        
    # If required empty the table first
    if empty:
        with engine.connect() as conn:
            stmt = delete(GGTaxon)
            conn.execute(stmt)

    new_taxons = []
    taxon_count = 0

    # read the taxonomy file
    with open(gg_taxonomy_data, 'r') as file:
        lines = file.readlines()

        for line in lines:

            # split the line into the taxonomy information
            line = line.strip().split('\t')

            # add the taxonomy information to the database
            new_taxon = GGTaxon(**{"gg_id": line[0],
                                    "taxon_path": line[1]})

            session.add(new_taxon)
            new_taxons.append(new_taxon)
            taxon_count += 1

        # add 400 taxons at the time, more can cause problems with some database engines
        if len(new_taxons) > 400:
            session.commit()
            new_taxons = []

    # add the last set of sequences
    session.commit()

    return taxon_count

def add_gtdb_taxonomy(gtdb_taxonomy_data, gtdb_release, empty=True):
    """
    Adds GTDB taxonomy information to the database.

    :param taxonomy_data: GTDB taxonomy data (e.g., bac120_taxonomy_r220.tsv, for Bacteria)
    :param release: GTDB release number (e.g., 214)
    #TODO: store release number in the database
    :param empty: Empty the database first when true (default: True)
    :return: 
    """

    # If required empty the table first
    if empty:
        with engine.connect() as conn:
            stmt = delete(GTDBTaxon)
            conn.execute(stmt)

    new_taxons = []
    taxon_count = 0

    # read the taxonomy file
    with open(gtdb_taxonomy_data, 'r') as file:
        lines = file.readlines()

        for line in lines:

            # split the line into the taxonomy information
            line = line.strip().split('\t')

            # add the taxonomy information to the database
            new_taxon = GTDBTaxon(**{"gtdb_id": line[0],
                                    "taxon_path": line[1]})

            session.add(new_taxon)
            new_taxons.append(new_taxon)
            taxon_count += 1

        # add 400 taxons at the time, more can cause problems with some database engines
        if len(new_taxons) > 400:
            session.commit()
            new_taxons = []

    # add the last set of sequences
    session.commit()

    return taxon_count

db_admin = args.db_admin
db_name = args.db_name
silva_taxonomy_file = args.silva_taxonomy_file
silva_release = args.silva_release
gg_taxonomy_file = args.gg_taxonomy_file
gg_release = args.gg_release
gtdb_taxonomy_file = args.gtdb_taxonomy_file
gtdb_release = args.gtdb_release

taxonomy_data_count = 0

if silva_taxonomy_file:
    taxonomy_data_count+=1

if gg_taxonomy_file:
    taxonomy_data_count+=1

if gtdb_taxonomy_file:
    taxonomy_data_count+=1

if taxonomy_data_count == 0:
    print("Must add at least one type of taxonomy databases (e.g., --silva_taxonomy_file)\
          to the database!")
    exit(1)

create_engine_string = "mysql+pymysql://"+db_admin+":"+db_password+"@localhost/"+db_name

engine = create_engine(create_engine_string, echo=True)

# Reflect an existing database into a new model
Base = automap_base()

Base.prepare(engine, reflect=True)

SILVATaxon = Base.classes.silva_taxonomy
GGTaxon = Base.classes.gg_taxonomy
GTDBTaxon = Base.classes.gtdb_taxonomy

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()

if silva_taxonomy_file:
    if silva_release:
        add_silva_taxonomy(silva_taxonomy_file, silva_release)
    else:
        print("Must provide the SILVA release number!")
        exit(1)

if gg_taxonomy_file:
    if gg_release:
        add_gg_taxonomy(gg_taxonomy_file, gg_release)
    else:
        print("Must provide the GreenGenes release number!")
        exit(1)

if gtdb_taxonomy_file:
    if gtdb_release:
        add_gtdb_taxonomy(gtdb_taxonomy_file, gtdb_release)
    else:
        print("Must provide the GTDB release number!")
        exit(1)

session.close()