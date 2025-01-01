#!/usr/bin/env python3

import argparse
import gzip
import operator
import sys

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select

from crossref.restful import Works

parser = argparse.ArgumentParser(description='Add samples to the database')
parser.add_argument('--fasta_file', type=str, metavar='otus.fasta',
                    dest='fasta_file',
                    help='FASTA file with OTUs to add to the database',
                    required=True)
parser.add_argument('--literature_doi', type=str, metavar='10.1094/PBIOMES-02-18-0008-R',
                    dest='literature_doi',
                    help='The DOI of the literature article that generation of OTUs',
                    required=True)
parser.add_argument('--amplicon_marker', type=str, metavar='16S',
                    dest='amplicon_marker',
                    help='Marker used to generate OTUs (16S or ITS)',
                    required=True)
parser.add_argument('--primer_pair', type=str, metavar='515F-1401R',
                    dest='primer_pair',
                    help='Primer pair used to generate OTUs',
                    required=True)
parser.add_argument('--method_description', type=str, metavar='Brief description of the method used to generate OTUs',
                    dest='otu_method_description',
                    help='Brief description of the method used to generate OTUs',
                    required=True)
parser.add_argument('--clustering_method', type=str, metavar='de_novo',
                    dest='otu_clustering_method',
                    help='Clustering method used to generate OTUs',
                    required=True)
parser.add_argument('--clustering_algorithm', type=str, metavar='qiime1',
                    dest='otu_clustering_algorithm',
                    help='Clustering algorithm used to generate OTUs',
                    required=True)
parser.add_argument('--clustering_threshold', type=float, metavar='0.97',
                    dest='otu_clustering_threshold',
                    help='Clustering threshold used to generate OTUs',
                    required=True)
parser.add_argument('--clustering_reference_db', type=str, metavar='greengenes',
                    dest='clustering_reference_db',
                    help='Clustering reference database used to generate OTUs',
                    required=True)
parser.add_argument('--clustering_reference_db_release', type=str, metavar='13_5',
                    dest='clustering_reference_db_release',
                    help='Release of the clustering reference database used to generate OTUs',
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


class Fasta:
    def __init__(self):
        self.sequences = {}

    def remove_subset(self, length):
        """
        Removes a set of sequences and returns those as a subset

        :param length: number of sequences to remove
        :return: Fasta object with the sequences removed from the current one
        """
        output = Fasta()
        keys = list(self.sequences.keys())
        output.sequences = {k: self.sequences[k] for k in keys[:length]}

        self.sequences = {k: self.sequences[k] for k in keys[length:]}

        return output

    def readfile(self, filename, compressed=False, verbose=False):
        """
        Reads a fasta file to the dictionary

        :param filename: file to read
        :param compressed: set to true if reading form a gzipped file
        :param verbose: set to true to get extra debug information printed to STDERR
        """
        if verbose:
            print("Reading FASTA file:" + filename + "...", file=sys.stderr)

        # Initialize variables
        name = ''
        sequence = []
        count = 1

        # open file
        if compressed:
            f = gzip.open(filename, 'rt')
        else:
            f = open(filename, 'r')

        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                # ignore if first
                if not name == '':
                    self.sequences[name] = ''.join(sequence)
                    count += 1
                name = line.lstrip('>')
                sequence = []
            else:
                sequence.append(line)

        # add last gene
        self.sequences[name] = ''.join(sequence)

        f.close()
        if verbose:
            print("Done! (found ", count, " sequences)", file=sys.stderr)

    def writefile(self, filename):
        """
        writes the sequences back to a fasta file

        :param filename: file to write to
        """
        with open(filename, 'w') as f:
            for k, v in self.sequences.items():
                print(">" + k, file=f)
                print(v, file=f)


def add_literature(doi, engine):

        works = Works()
        # verify if DOI already exists in DB, if not, collect data
        literature_info = works.doi(doi)

        qtd_author = len(literature_info['author'])
        
        if 'family' in literature_info['author'][0].keys():
            author_names = literature_info['author'][0]['family']
        else:
            author_names = literature_info['author'][0]['name']

        title = literature_info['title']
        
        if 'published-print' in literature_info.keys():
            public_year = literature_info['published-print']['date-parts'][0][0]
        elif 'published-online' in literature_info.keys():
            public_year = literature_info['published-online']['date-parts'][0][0]
        else:
            public_year = literature_info['issued']['date-parts'][0][0]

        new_literature = LiteratureItem(qtd_author=qtd_author,
                                        author_names=author_names,
                                        title=title,
                                        public_year=public_year,
                                        doi=doi)
    
        with engine.connect() as conn:
            stmt = select(LiteratureItem).where(LiteratureItem.__table__.c.doi == doi)
            literature = conn.execute(stmt).first()

        # literature is not in the DB yet, add it
        if not literature:
            session.add(new_literature)
            session.commit()

            return new_literature.id
        else:
            return literature.id


def add_otus_from_fasta(otus_fasta,
                            otu_method_description,
                            clustering_method,
                            clustering_threshold,
                            clustering_algorithm,
                            clustering_reference_database,
                            clustering_reference_db_release,
                            amplicon_marker,
                            primer_pair, literature_doi):
        
    """
    Function to add OTU representative sequences to the database

    :param otus_fasta: path to the file with OTU representative sequences
    :param otu_method_description: description of the OTU method
    :param clustering_method: clustering method used to generate OTUs (e.g. de novo)
    :param clustering_threshold: threshold used for clustering (e.g. 97%)
    :param clustering_algorithm: algorithm used for clustering (e.g. qiime1)
    :param clustering_reference_database: reference database used for clustering (e.g. greengenes)
    :param clustering_reference_db_release: release of the reference database
    :param amplicon_marker: marker (currently 16S or ITS)
    :param primer_pair: primer pair used to generate amplicons
    :param literature_doi: DOI of the publication describing the method
    """

    if clustering_method in ['closed_reference', 'open_reference']:
        if not clustering_reference_database:
            raise ValueError("Reference database is required for closed or open reference OTU picking")

    fasta_data = Fasta()
    fasta_data.readfile(otus_fasta)

    # add literature
    if literature_doi:
        literature_id = add_literature(literature_doi, engine)
    else:
        print("No literature DOI provided, but it is required for adding OTUs")
        exit(1)

    # Add OTU method
    new_otu_method = OperationalTaxonomicUnitMethod(**{"description": otu_method_description,
                                                    "clustering_method": clustering_method,
                                                    "clustering_threshold": clustering_threshold,
                                                    "clustering_algorithm": clustering_algorithm,
                                                    "clustering_reference_database": clustering_reference_database,
                                                    "clustering_reference_db_release": clustering_reference_db_release,
                                                    "amplicon_marker": amplicon_marker,
                                                    "primer_pair": primer_pair,
                                                    "literature_id": literature_id})

    session.add(new_otu_method)
    session.commit()

    added_otus = []
    new_otus = []

    # Loop over OTUs and add to db
    for name, sequence in sorted(fasta_data.sequences.items(), key=operator.itemgetter(0)):
        
        if name not in added_otus:
            added_otus.append(name)
        
        new_otu = OperationalTaxonomicUnit(**{"original_id": name,
                                            "representative_sequence": sequence,
                                            "method_id": new_otu_method.id})

        session.add(new_otu)
        new_otus.append(new_otu)

        # add 400 sequences at the time, more can cause problems with some database engines
        if len(new_otus) > 400:
            session.commit()
            new_otus = []

    # add the last set of sequences
    session.commit()

    return len(fasta_data.sequences.keys())


fasta_file = args.fasta_file
literature_doi = args.literature_doi
amplicon_marker = args.amplicon_marker
primer_pair = args.primer_pair
method_description = args.otu_method_description
otu_clustering_method = args.otu_clustering_method
otu_clustering_algorithm = args.otu_clustering_algorithm
otu_clustering_threshold = args.otu_clustering_threshold
clustering_reference_db = args.clustering_reference_db
clustering_reference_db_release = args.clustering_reference_db_release
db_admin = args.db_admin
db_name = args.db_name

create_engine_string = "mysql+pymysql://"+db_admin+":"+db_password+"@localhost/"+db_name

engine = create_engine(create_engine_string, echo=True)

# Reflect an existing database into a new model
Base = automap_base()

Base.prepare(engine, reflect=True)

OperationalTaxonomicUnitMethod = Base.classes.otu_methods
LiteratureItem = Base.classes.literature
OperationalTaxonomicUnit = Base.classes.otus

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()

# Run function to add OTUs to the database
add_otus_from_fasta(fasta_file,
                            method_description,
                            otu_clustering_method,
                            otu_clustering_threshold,
                            otu_clustering_algorithm,
                            clustering_reference_db,
                            clustering_reference_db_release,
                            amplicon_marker,
                            primer_pair, literature_doi)

session.close()





