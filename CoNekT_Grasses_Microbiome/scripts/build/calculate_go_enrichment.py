#!/usr/bin/env python3

import argparse

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

from sqlalchemy.sql import delete, select

# Create arguments
parser = argparse.ArgumentParser(description='Calculate cluster GO enrichment and add to database')
parser.add_argument('--', type=int, metavar='1',
                    dest='network_method_id',
                    help='The network method ID',
                    required=True)
parser.add_argument('--description', type=str, metavar='Description',
                    dest='clustering_method_description',
                    help='Description of the clustering as it should appear in CoNekT Grasses',
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

def __calculate_enrichment(self):
    """
    Initial implementation to calculate GO enrichment for a single cluster
    """
    gene_count = self.method.network_method.species.sequence_count
    species_id = self.method.network_method.species_id

    sequences = self.sequences.options(load_only("id")).all()

    associations = SequenceGOAssociation.query\
        .filter(SequenceGOAssociation.sequence_id.in_([s.id for s in sequences]))\
        .filter(SequenceGOAssociation.predicted == 0)\
        .options(load_only("sequence_id", "go_id"))\
        .group_by(SequenceGOAssociation.sequence_id, SequenceGOAssociation.go_id)

    go_data = {}

    for a in associations:
        if a.go_id not in go_data.keys():
            go_data[a.go_id] = {}
            go_data[a.go_id]["total_count"] = json.loads(a.go.species_counts)[str(species_id)]
            go_data[a.go_id]["cluster_count"] = 1
        else:
            go_data[a.go_id]["cluster_count"] += 1

    p_values = []
    for go_id in go_data:
        p_values.append(hypergeo_sf(go_data[go_id]['cluster_count'],
                                    len(sequences),
                                    go_data[go_id]['total_count'],
                                    gene_count))

    corrected_p_values = fdr_correction(p_values)

    for i, go_id in enumerate(go_data):
        enrichment = ClusterGOEnrichment()
        enrichment.cluster_id = self.id
        enrichment.go_id = go_id

        enrichment.cluster_count = go_data[go_id]['cluster_count']
        enrichment.cluster_size = len(sequences)
        enrichment.go_count = go_data[go_id]['total_count']
        enrichment.go_size = gene_count

        enrichment.enrichment = log2((go_data[go_id]['cluster_count']/len(sequences))/(go_data[go_id]['total_count']/gene_count))
        enrichment.p_value = p_values[i]
        enrichment.corrected_p_value = corrected_p_values[i]

        db.session.add(enrichment)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)


def calculate_enrichment(engine, empty=True):
    """
    Static method to calculate the enrichment for all cluster in the database

    :param empty: empty table cluster_go_enrichment first
    """

    # If required empty the table first
    if empty:
        with engine.connect() as conn:
            stmt = delete(ClusterGOEnrichment)
            conn.execute(stmt)

    with engine.connect() as conn:
        stmt = select(ClusterGOEnrichment)
        clusters = conn.execute(stmt).all()

    for i, cluster in enumerate(clusters):
        cluster.__calculate_enrichment()

db_admin = args.db_admin
db_name = args.db_name

create_engine_string = "mysql+pymysql://"+db_admin+":"+db_password+"@localhost/"+db_name

engine = create_engine(create_engine_string, echo=True)

# Reflect an existing database into a new model
Base = automap_base()

# Use the engine to reflect the database
Base.prepare(engine, reflect=True)

CoexpressionCluster = Base.classes.coexpression_clusters
SequenceGOAssociation = Base.classes.sequence_go
ClusterGOEnrichment = Base.classes.cluster_go_enrichment

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()

# Run the function to calculate GO enrichment
calculate_enrichment(engine)

session.close()