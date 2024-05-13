"""
Set of functions to export the database to the ftp directory
"""
import csv
import gzip
import os

from flask import current_app
from sqlalchemy.orm import joinedload, noload

from conekt import create_app, db
from conekt.models.expression.coexpression_clusters import CoexpressionClusteringMethod
from conekt.models.expression.networks import ExpressionNetworkMethod, ExpressionNetwork
from conekt.models.gene_families import GeneFamilyMethod
from conekt.models.relationships.sequence_cluster import SequenceCoexpressionClusterAssociation
from conekt.models.relationships.sequence_family import SequenceFamilyAssociation
from conekt.models.relationships.sequence_go import SequenceGOAssociation
from conekt.models.relationships.sequence_cazyme import SequenceCAZYmeAssociation
from conekt.models.sequences import Sequence
from conekt.models.species import Species

from utils.sequence import translate


# TODO: rewrite some of these methods using ORM free database interactions
def export_coding_sequences(SEQUENCE_PATH):
    """
    Exports sequences for transcripts as gzipped fasta files to the desired path
    """
    if not os.path.exists(SEQUENCE_PATH):
        os.makedirs(SEQUENCE_PATH)

    species = Species.query.all()

    for s in species:
        filename = s.code + ".cds.fasta.gz"
        filename = os.path.join(SEQUENCE_PATH, filename)
        sequences = db.engine.execute(db.select([Sequence.__table__.c.name, Sequence.__table__.c.coding_sequence]).
                                      where(Sequence.__table__.c.species_id == s.id)
                                      ).fetchall()

        with gzip.open(filename, 'wb') as f:
            for (name, coding_sequence) in sequences:
                f.write(bytes(">" + name + '\n' + coding_sequence + '\n', 'UTF-8'))


def export_protein_sequences(SEQUENCE_PATH):
    """
    Exports amino acid sequences for protein_coding transcripts as gzipped fasta files to the desired path
    """
    if not os.path.exists(SEQUENCE_PATH):
        os.makedirs(SEQUENCE_PATH)

    species = Species.query.all()

    for s in species:
        filename = s.code + ".aa.fasta.gz"
        filename = os.path.join(SEQUENCE_PATH, filename)

        sequences = db.engine.execute(db.select([Sequence.__table__.c.name, Sequence.__table__.c.type, Sequence.__table__.c.coding_sequence]).
                                      where(Sequence.__table__.c.species_id == s.id)
                                      ).fetchall()

        with gzip.open(filename, 'wb') as f:
            for (name, sequence_type, sequence) in sequences:
                if sequence_type == "protein_coding":
                    f.write(bytes(">" + name + '\n' + translate(sequence) + '\n', 'UTF-8'))


def export_go_annotation(ANNOTATION_PATH):
    """
    Export GO annotation for each sequence
    """
    if not os.path.exists(ANNOTATION_PATH):
        os.makedirs(ANNOTATION_PATH)

    species = Species.query.all()

    for s in species:
        filename = s.code + ".go.csv.gz"
        filename = os.path.join(ANNOTATION_PATH, filename)

        sequences = s.sequences.options(noload('xrefs')).all()

        with gzip.open(filename, 'wt') as f:
            csv_out = csv.writer(f, lineterminator='\n')
            for count, sequence in enumerate(sequences):
                # print(count, sequence.name)
                go_associations = sequence.go_associations.filter(SequenceGOAssociation.source is not None).all()
                for go_association in go_associations:
                     csv_out.writerow([sequence.name,
                                      sequence.species.code,
                                      go_association.go.label,
                                      go_association.go.name,
                                      go_association.go.type,
                                      go_association.source])


def export_interpro_annotation(ANNOTATION_PATH):
    """
    Export interpro annotation for each sequence
    """
    if not os.path.exists(ANNOTATION_PATH):
        os.makedirs(ANNOTATION_PATH)

    species = Species.query.all()

    for s in species:
        filename = s.code + ".interpro.csv.gz"
        filename = os.path.join(ANNOTATION_PATH, filename)

        sequences = s.sequences.options(noload('xrefs')).all()

        with gzip.open(filename, 'wt') as f:
            csv_out = csv.writer(f, lineterminator='\n')
            for count, sequence in enumerate(sequences):
                interpo_associations = sequence.interpro_associations.all()
                for interpro_association in interpo_associations:
                     csv_out.writerow([sequence.name,
                                      sequence.species.code,
                                      interpro_association.domain.label,
                                      interpro_association.domain.description,
                                      interpro_association.start,
                                      interpro_association.stop])


def export_cazyme_annotation(ANNOTATION_PATH):
    """
    Export cazyme annotation for each sequence
    """
    if not os.path.exists(ANNOTATION_PATH):
        os.makedirs(ANNOTATION_PATH)

    species = Species.query.all()

    for s in species:
        filename = s.code + ".cazyme.csv.gz"
        filename = os.path.join(ANNOTATION_PATH, filename)

        sequences = s.sequences.options(noload('xrefs')).all()

        with gzip.open(filename, 'wt') as f:
            csv_out = csv.writer(f, lineterminator='\n')
            for count, sequence in enumerate(sequences):
                cazyme_associations = sequence.cazyme_associations.all()
                for cazyme_association in cazyme_associations:
                     csv_out.writerow([sequence.name,
                                      sequence.species.code,
                                      cazyme_association.cazyme.family,
                                      cazyme_association.hmm_length,
                                      cazyme_association.query_length, 
                                      cazyme_association.e_value,
                                      cazyme_association.query_start, 
                                      cazyme_association.query_stop])


def export_families(FAMILIES_PATH):
    """
    Export gene families and an overview of the methods to generate them
    """
    if not os.path.exists(FAMILIES_PATH):
        os.makedirs(FAMILIES_PATH)

    methods = GeneFamilyMethod.query.all()

    methodsfile = os.path.join(FAMILIES_PATH, 'methods_overview.txt')

    with open(methodsfile, "w") as f:
        for m in methods:
            print(m.id, m.method, m.family_count, file=f, sep='\t')

    associations = SequenceFamilyAssociation.query.all()

    output = {}

    for a in associations:
        if a.family.method_id not in output.keys():
            output[a.family.method_id] = {}

        if a.family.name not in output[a.family.method_id].keys():
            output[a.family.method_id][a.family.name] = []

        output[a.family.method_id][a.family.name].append(a.sequence.name)

    for method, families in sorted(output.items()):
        familyfile = os.path.join(FAMILIES_PATH, 'families_method_'+str(method)+'.tab')
        with open(familyfile, "w") as f:
            for family, members in sorted(families.items()):
                print(method, family, ";".join(members), file=f, sep='\t')


def export_coexpression_clusters(EXPRESSION_PATH):
    """
    Export coexpression clusters and an overview of the methods to generate them
    """
    if not os.path.exists(EXPRESSION_PATH):
        os.makedirs(EXPRESSION_PATH)

    methods = CoexpressionClusteringMethod.query.all()

    methodsfile = os.path.join(EXPRESSION_PATH, 'clustering_methods_overview.txt')

    with open(methodsfile, "w") as f:
        for m in methods:
            print(m.id, m.network_method.species.code, m.method, m.cluster_count, file=f, sep='\t')

    associations = SequenceCoexpressionClusterAssociation.query.all()

    output = {}

    for a in associations:
        if a.coexpression_cluster.method_id not in output.keys():
            output[a.coexpression_cluster.method_id] = {}

        if a.coexpression_cluster.name not in output[a.coexpression_cluster.method_id].keys():
            output[a.coexpression_cluster.method_id][a.coexpression_cluster.name] = []

        if a.sequence is not None:
            output[a.coexpression_cluster.method_id][a.coexpression_cluster.name].\
                append(a.sequence.name + "(" + a.probe + ")")
        else:
            output[a.coexpression_cluster.method_id][a.coexpression_cluster.name].\
                append("None(" + a.probe + ")")

    for method, clusters in sorted(output.items()):
        clusterfile = os.path.join(EXPRESSION_PATH, 'clustering_method_'+str(method)+'.tab')
        with open(clusterfile, "w") as f:
            for cluster, members in sorted(clusters.items()):
                print(method, cluster, ";".join(members), file=f, sep='\t')


def export_expression_networks(EXPRESSION_PATH):
    """
    Export expression networks and an overview of the methods to generate them
    """
    if not os.path.exists(EXPRESSION_PATH):
        os.makedirs(EXPRESSION_PATH)

    networks = ExpressionNetworkMethod.query.all()

    methodsfile = os.path.join(EXPRESSION_PATH, 'network_methods_overview.txt')
    with open(methodsfile, "w") as f:
        for n in networks:
            print(n.id, n.species.code, n.description, n.probe_count, file=f, sep='\t')

    for n in networks:
        networkfile = os.path.join(EXPRESSION_PATH, 'network_method_'+str(n.id)+'.tab.gz')
        with gzip.open(networkfile, "wb") as f:
            # Get all probes for the network (using a joined load to avoid hammering the database)
            probes = ExpressionNetwork.query.filter(ExpressionNetwork.method_id == n.id).\
                options(joinedload('sequence').load_only('name')).all()
            for probe in probes:
                if probe.sequence_id is not None:
                    out = '\t'.join([n.species.code, probe.probe, probe.sequence.name, probe.network]) + '\n'
                    f.write(bytes(out, 'UTF-8'))
                else:
                    out = '\t'.join([n.species.code, probe.probe, "None", probe.network]) + '\n'
                    f.write(bytes(out, 'UTF-8'))


def export_ftp_data(configuration):
    """
    Export all data
    """
    app = create_app(configuration)

    with app.app_context():

        PLANET_FTP_DATA = current_app.config['PLANET_FTP_DATA']

        # Constants for the sub-folders
        SEQUENCE_PATH = os.path.join(PLANET_FTP_DATA, 'sequences')
        ANNOTATION_PATH = os.path.join(PLANET_FTP_DATA, 'annotation')
        FAMILIES_PATH = os.path.join(PLANET_FTP_DATA, 'families')
        EXPRESSION_PATH = os.path.join(PLANET_FTP_DATA, 'expression')

        export_coding_sequences(SEQUENCE_PATH)
        export_protein_sequences(SEQUENCE_PATH)

        export_go_annotation(ANNOTATION_PATH)
        export_interpro_annotation(ANNOTATION_PATH)
        export_cazyme_annotation(ANNOTATION_PATH)

        export_families(FAMILIES_PATH)
        export_coexpression_clusters(EXPRESSION_PATH)
        export_expression_networks(EXPRESSION_PATH)
