#!/usr/bin/env python3

import argparse

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from collections import defaultdict

from crossref.restful import Works

parser = argparse.ArgumentParser(description='Add samples to the database')
parser.add_argument('--species_code', type=str, metavar='Svi',
                    dest='species_code',
                    help='The CoNekT Microbiome species code',
                    required=True)
parser.add_argument('--sample_annotation', type=str, metavar='sample_annotation.tsv',
                    dest='sample_annotation_file',
                    help='The TSV file with sample annotation',
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


def add_sample_po_association(sample, po_term):
        
    with engine.connect() as conn:
        stmt = select(PlantOntology).where(PlantOntology.__table__.c.po_term == po_term)
        po = conn.execute(stmt).first()
    species_id = sample.species_id
    
    association = {'sample_id': sample.id,
                    'po_id': po.id,
                    'species_id': species_id}

    session.execute(SamplePOAssociation.__table__.insert(), association)

def add_sample_peco_association(sample, peco_term):

    with engine.connect() as conn:
        stmt = select(PlantExperimentalConditionsOntology).where(PlantExperimentalConditionsOntology.__table__.c.peco_term == peco_term)
        peco = conn.execute(stmt).first()
    species_id = sample.species_id

    association = {'sample_id': sample.id,
                    'peco_id': peco.id,
                    'species_id': species_id}

    session.execute(SamplePECOAssociation.__table__.insert(), association)

def add_sample_envo_association(sample, envo_term):

    with engine.connect() as conn:
        stmt = select(EnvironmentOntology).where(EnvironmentOntology.__table__.c.envo_term == envo_term)
        envo = conn.execute(stmt).first()
    species_id = sample.species_id

    association = {'sample_id': sample.id,
                    'envo_id': envo.id,
                    'species_id': species_id}

    session.execute(SampleENVOAssociation.__table__.insert(), association)

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


def add_samples_from_file(samples_file, species_code):
    """Add samples from a tabular file to the database.
    
    returns the number of samples added to the database.
    """

    # Check if species exists in the database
    with engine.connect() as conn:
        stmt = select(Species).where(Species.__table__.c.code == species_code)
        species = conn.execute(stmt).first()

    if not species:
        print(f"Species ({species_code}) not found in the database.")
        exit(1)
    else:
        species_id = species.id

    sample_count = 0

    # read the samples file
    with open(samples_file, 'r') as file:
        # get rid of the header
        _ = file.readline()

        lines = file.readlines()

        for line in lines:
            
            # split the line into the sample information
            parts = line.strip().split('\t')

            sample_name = parts[0]
            doi = parts[1]
            condition_description = parts[2]
            replicate = int(parts[3])

            # get the ontology terms, if they exist
            try:
                po_anatomy_term = parts[4]
            except IndexError:
                po_anatomy_term = None
                print("Warning: PO term not found for this sample")

            try:
                po_dev_stage_term = parts[5]
            except IndexError:
                po_dev_stage_term = None
                print("Warning: PO term not found for this sample")

            try:
                peco_term = parts[6]
            except IndexError:
                peco_term = None
                print("Warning: PECO term not found for this sample")

            try:
                envo_term = parts[7]
            except IndexError:
                envo_term = None
                print("Warning: ENVO term not found for this sample")
            
            try:
                species_genotype = parts[8]
            except IndexError:
                species_genotype = None
                print("Warning: Genotype term not found for this sample")

            with engine.connect() as conn:
                stmt = select(LiteratureItem).where(LiteratureItem.__table__.c.doi == doi)
                literature = conn.execute(stmt).first()

            if literature is None:
                literature_id = add_literature(doi, engine)
            else:
                literature_id = literature.id

            # add the sample to the database
            new_sample = {"name": sample_name,
                          "description": condition_description,
                          "replicate": replicate,
                          "species_id": species_id,
                          "literature_id": literature_id,
                          "species_genotype": species_genotype}

            session.add(Sample(**new_sample))
            session.commit()
            sample_count += 1

            with engine.connect() as conn:
                stmt = select(Sample).where(Sample.__table__.c.name == sample_name)
                new_sample = conn.execute(stmt).first()

            try:
                sample_group_definitions = parts[9]
                sample_groups = sample_group_definitions.split(';')
                for sample_group in sample_groups:
                    group_type, group_name = sample_group.split(':')
                    if group_type.startswith(' '):
                        group_type = group_type.replace(' ', '', 1)
                    sample_group_association = {"sample_id": new_sample.id,
                                                "group_type": group_type,
                                                "group_name": group_name}
                    session.add(SampleGroupAssociation(**sample_group_association))
            except IndexError:
                sample_group_definitions = None
                print("Warning: Group(s) was/were not defined for this sample")

            if po_anatomy_term:
                if po_anatomy_term.startswith('PO:'):
                    add_sample_po_association(new_sample, po_anatomy_term)

            if po_dev_stage_term:
                if po_dev_stage_term.startswith('PO:'):
                    add_sample_po_association(new_sample, po_dev_stage_term)
            
            if peco_term:
                if peco_term.startswith('PECO:'):
                    add_sample_peco_association(new_sample, peco_term)
            
            if envo_term:
                if envo_term.startswith('ENVO:'):
                    add_sample_envo_association(new_sample, envo_term)

            session.commit()

    return sample_count

sps_code = args.species_code
sample_annotation_file = args.sample_annotation_file
db_admin = args.db_admin
db_name = args.db_name

create_engine_string = "mysql+pymysql://"+db_admin+":"+db_password+"@localhost/"+db_name

engine = create_engine(create_engine_string, echo=True)

# Reflect an existing database into a new model
Base = automap_base()

Base.prepare(engine, reflect=True)

Species = Base.classes.species
Sample = Base.classes.samples
PlantExperimentalConditionsOntology = Base.classes.plant_experimental_conditions_ontology
PlantOntology = Base.classes.plant_ontology
EnvironmentOntology = Base.classes.environment_ontology
LiteratureItem = Base.classes.literature
SampleGroupAssociation = Base.classes.sample_groups
SamplePOAssociation = Base.classes.sample_po
SamplePECOAssociation = Base.classes.sample_peco
SampleENVOAssociation = Base.classes.sample_envo

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()

# Run function to add samples to the database
add_samples_from_file(sample_annotation_file, sps_code)

session.close()