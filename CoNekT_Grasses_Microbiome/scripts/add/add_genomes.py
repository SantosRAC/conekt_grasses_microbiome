#!/usr/bin/env python3

import argparse
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import delete
from conekt.models.geocode_utils import geocode_location

# Create arguments
parser = argparse.ArgumentParser(description='Add genomes data to the database')
parser.add_argument('--genome', type=str, metavar='genome.txt',
                    dest='genomes_file',
                    help='The genomes information file',
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


def add_genomes_from_file(genomes_file, empty = True):
    """Add genomes from a tabular file to the database.
    
    returns the number of genomes added to the database.
    """

    # If required empty the table first
    file_size = os.stat(genomes_file).st_size
    if empty and file_size > 0:
        # If required empty the table first
        with engine.connect() as conn:
            stmt = delete(Genome)
            conn.execute(stmt)
            conn.commit()

    genome_count = 0

    # read the genomes file
    with open(genomes_file, 'r') as file:
        # get rid of the header
        _ = file.readline()

        lines = file.readlines()

        for line in lines:
            # split the line into the genome information
            parts = line.strip().split('\t')

            genome_id = parts[0]
            doi = parts[1]
            genome_type = parts[2]
            length = int(parts[3])
            N50 = int(parts[4])
            gc_perc = float(parts[5])
            num_contigs = int(parts[6])
            cluster_id = int(parts[7])
            representative = parts[8]
            completeness = float(parts[9])
            contamination = float(parts[10])
            quality = parts[11]
            rrna_16S = parts[12]
            copies_16S = parts[13]
            country = parts[14]
            local = parts[15]
            lat = parts[16]
            lon = parts[17]

            # get the ontology terms, if they exist habitat
            try:
                envo_habitat = parts[18]
            except IndexError:
                envo_habitat = None
                print('Warning: ENVO term not found for this genome')

            # get the ontology terms, if they exist isolation source
            try:
                envo_isolation_source = parts[19]
            except IndexError:
                envo_isolation_source = None
                print('Warning: ENVO term not found for this genome')
            
            ncbi_accession = parts[20]
            biosample = parts[21]
            bioproject = parts[22]

                 
            if doi.lower() == 'unpublished':
                literature_id = None # or any other indicator for unpublished
            else:
                literature = LiteratureItem.query.filter_by(doi=doi).first()

                if literature is None:
                    literature_id = LiteratureItem.add(doi)
                else:
                    literature_id = literature.id

            # add the genome to the database
            new_genome = Genome(genome_id, genome_type, length, N50, gc_perc, num_contigs, cluster_id, representative, literature_id) 

            session.add(new_genome)

            # add the genome quality to the database
            new_genome_quality_info = GenomesQuality(genome_id, completeness,contamination, quality, rrna_16S, copies_16S)
            session.add(new_genome_quality_info)

            # Add the geographic information to the database

            # Formating the coordinates
            if not lat or not lon:
                lat, lon = geocode_location(country, local)
            if not lat or not lon:
                print(f"Geocoding failed for {local}, {country}. No coordinates found.")
                lat = None
                lon = None

            new_geographic_info = Geographic(genome_id, country, local, lat, lon)

            session.add(new_geographic_info)

            # add the envo to the database
            new_genome_envo = GenomeENVO(genome_id, envo_habitat, envo_isolation_source)
            session.add(new_genome_envo)

            # add NCBI information to the database
            new_ncbi_information = NCBI(genome_id, ncbi_accession, biosample, bioproject)
            session.add(new_ncbi_information)

        session.commit()

        genome_count += 1

db_admin = args.db_admin
db_name = args.db_name

create_engine_string = "mysql+pymysql://"+db_admin+":"+db_password+"@localhost/"+db_name

engine = create_engine(create_engine_string, echo=True)

# Reflect an existing database into a new model
Base = automap_base()

Base.prepare(engine, reflect=True)

Genome = Base.classes.genome
NCBI = Base.classes.NCBI
GenomeENVO = Base.classes.GenomeENVO
Geographic = Base.classes.Geographic
GenomesQuality = Base.classes.GenomesQuality
LiteratureItem = Base.classes.LiteratureItem


# Create a Session
Session = sessionmaker(bind=engine)
session = Session()


