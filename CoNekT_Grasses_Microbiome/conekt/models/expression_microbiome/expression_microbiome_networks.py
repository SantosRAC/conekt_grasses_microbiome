from flask import url_for
from conekt import db

from conekt.models.relationships.sequence_family import SequenceFamilyAssociation
from conekt.models.gene_families import GeneFamily
from conekt.models.sequences import Sequence

from utils.jaccard import jaccard
from utils.benchmark import benchmark

import random
import json
import re
import sys
from sqlalchemy import and_

from collections import defaultdict

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class ExpressionNetworkMethod(db.Model):
    __tablename__ = 'expression_network_methods'
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), index=True)
    description = db.Column(db.Text)
    edge_type = db.Column(db.Enum("rank", "weight", name='edge_type'))
    probe_count = db.Column(db.Integer)

    hrr_cutoff = db.Column(db.Integer)
    pcc_cutoff = db.Column(db.Float)
    enable_second_level = db.Column(db.SmallInteger)

    probes = db.relationship('ExpressionNetwork',
                             backref=db.backref('method', lazy='joined'),
                             lazy='dynamic',
                             cascade="all, delete-orphan",
                             passive_deletes=True)

    clustering_methods = db.relationship('CoexpressionClusteringMethod',
                                         backref='network_method',
                                         lazy='dynamic',
                                         cascade='all, delete-orphan',
                                         passive_deletes=True)

    def __init__(self, species_id, description, edge_type="rank"):
        self.species_id = species_id
        self.description = description
        self.edge_type = edge_type
        self.enable_second_level = False

    def __repr__(self):
        return str(self.id) + ". " + self.description + ' [' + str(self.species) + ']'

    @staticmethod
    def update_count():
        """
        To avoid long count queries the number of networks for each method can be precalculated and stored in the
        database using this function
        """
        methods = ExpressionNetworkMethod.query.all()

        for m in methods:
            m.probe_count = m.probes.count()

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)

    @staticmethod
    @benchmark
    def calculate_ecc(network_method_ids, gene_family_method_id, max_size=100):
        """
        Function to calculate the ECC scores in and between genes of different networks

        ORM free method for speed !

        :param network_method_ids: array of networks (using their internal id !) to compare
        :param gene_family_method_id: internal id of the type of family methods to be used for the comparison
        """

        network_families = {}
        sequence_network = {}
        sequence_network_method = {}
        sequence_family = {}
        family_sequence = {}

        # Get all the network information and store in dictionary
        for n in network_method_ids:
            current_network = db.session.execute(db.select([ExpressionNetwork.__table__.c.sequence_id,
                                                           ExpressionNetwork.__table__.c.network,
                                                           ExpressionNetwork.__table__.c.method_id]).
                                                where(ExpressionNetwork.__table__.c.method_id == n).
                                                where(ExpressionNetwork.__table__.c.sequence_id.isnot(None))
                                                ).fetchall()

            for sequence, network, network_method_id in current_network:
                if sequence is not None:
                    sequence_network[int(sequence)] = network
                    sequence_network_method[int(sequence)] = int(network_method_id)

        # Get family data and store in dictionary
        current_families = db.session.execute(db.select([SequenceFamilyAssociation.__table__.c.sequence_id,
                                                        SequenceFamilyAssociation.__table__.c.gene_family_id,
                                                        GeneFamily.__table__.c.method_id]).
                                             select_from(SequenceFamilyAssociation.__table__.join(GeneFamily.__table__)).
                                             where(GeneFamily.__table__.c.method_id == gene_family_method_id)
                                             ).fetchall()

        for sequence, family, method in current_families:
            sequence_family[int(sequence)] = int(family)

            if family not in family_sequence.keys():
                family_sequence[int(family)] = []

            family_sequence[int(family)].append(int(sequence))

        # Create a dict (key = network) with the families present in that network
        # Families that occur multiple times should be present multiple times as this is used
        # to set threshholds later !

        for sequence, network_method in sequence_network_method.items():
            # ignore sequences without a family, ideally this shouldn't happen
            if network_method not in network_families.keys():
                network_families[network_method] = []

            if sequence in sequence_family.keys():
                family = sequence_family[sequence]
                network_families[network_method].append(family)

        # Determine threshold and p-value
        # A background model will be computed for each combination of networks, an ECC score will need to be better
        # than 95 % of the randomly found values to be considered significant

        thresholds = {}
        print("Starting permutation tests")
        for n in network_method_ids:
            thresholds[n] = {}
            for m in network_method_ids:
                thresholds[n][m] = ExpressionNetworkMethod.__set_thresholds(network_families[n],
                                                                            network_families[m],
                                                                            max_size=max_size)

        # Data loaded start calculating ECCs
        new_ecc_scores = []

        for family, sequences in family_sequence.items():
            for i in range(len(sequences) - 1):
                query = sequences[i]
                for j in range(i+1, len(sequences)):
                    target = sequences[j]
                    if query in sequence_network.keys() and target in sequence_network.keys() and query != target:
                        # Ignore genes with overlapping neighborhoods
                        if not ExpressionNetworkMethod.__neighborhoods_overlap(sequence_network[query], sequence_network[target]):
                            ecc, significant = ExpressionNetworkMethod.__ecc(sequence_network[query],
                                                                             sequence_network[target],
                                                                             sequence_family,
                                                                             thresholds[sequence_network_method[query]][sequence_network_method[target]],
                                                                             family,
                                                                             max_size=max_size)
                            if significant:
                                new_ecc_scores.append({
                                    'query_id': query,
                                    'target_id': target,
                                    'ecc': ecc,
                                    'gene_family_method_id': gene_family_method_id,
                                    'query_network_method_id': sequence_network_method[query],
                                    'target_network_method_id': sequence_network_method[target],
                                })

                                # add reciprocal relation
                                new_ecc_scores.append({
                                    'query_id': target,
                                    'target_id': query,
                                    'ecc': ecc,
                                    'gene_family_method_id': gene_family_method_id,
                                    'query_network_method_id': sequence_network_method[target],
                                    'target_network_method_id': sequence_network_method[query],
                                })
                                if len(new_ecc_scores) > 400:
                                    db.session.execute(SequenceSequenceECCAssociation.__table__.insert(), new_ecc_scores)
                                    new_ecc_scores = []

        db.session.execute(SequenceSequenceECCAssociation.__table__.insert(), new_ecc_scores)

    @staticmethod
    def __neighborhoods_overlap(neighborhood_a, neighborhood_b):
        """
        Checks if two genes have overlapping networks

        :param neighborhood_a: neighborhood for first gene (string as stored in database)
        :param neighborhood_b: neighborhood for second gene (string as stored in database)
        :return: Bool, true if networks overlap
        """
        genes_a = set([n['gene_id'] for n in json.loads(neighborhood_a) if n['gene_id'] is not None])
        genes_b = set([n['gene_id'] for n in json.loads(neighborhood_b) if n['gene_id'] is not None])

        return len(genes_a.intersection(genes_b)) > 0

    @staticmethod
    def __ecc(q_network, t_network, families, thresholds, query_family, max_size=30):
        """
        Takes the networks neighborhoods (as stored in the databases), extracts the genes and find the families for
        each gene. Next the ECC score is calculated

        :param q_network: network for the query gene
        :param t_network: network for the target gene
        :param families: dictionary that links a sequence id (key) to a family id (value)
        :param thresholds:
        :param query_family: name of the input gene family
        :return: the ECC score for the two input neighborhoods given the families, a boolean flag if this is significant
        """
        q_data = json.loads(q_network)
        t_data = json.loads(t_network)

        q_genes = [t['gene_id'] for t in q_data if t['gene_id'] is not None]
        t_genes = [t['gene_id'] for t in t_data if t['gene_id'] is not None]

        q_families = [families[q] for q in q_genes if q in families.keys() and families[q] != query_family]
        t_families = [families[t] for t in t_genes if t in families.keys() and families[t] != query_family]

        # print("***\nQuery %d\n%s\n%s" % (query_family, ','.join([str(q) for q in q_families]), ','.join([str(t) for t in t_families])))

        if len(q_families) == 0 or len(t_families) == 0:
            return 0.0, False
        else:
            ecc = jaccard(q_families, t_families)

            q_size = len(set(q_families)) if len(set(q_families)) < max_size else max_size
            t_size = len(set(t_families)) if len(set(t_families)) < max_size else max_size

            t = thresholds[q_size-1][t_size-1]

            return ecc, ecc > t

    @staticmethod
    @benchmark
    def __set_thresholds(families_a, families_b, max_size=30, iterations=1000, step=5):
        """
        Empirically determine (permutation test) thresholds for ECC

        :param families_a: families of species_a (list of internal family ids)
        :param families_b: families of species_b (list of internal family ids)
        :param max_size: maximum number of families (default = 30)
        :param iterations: number of permutations done
        :param step: step size
        :return: matrix (list of lists) with the thresholds at various family sizes
        """
        thresholds = []

        for i in range(0, max_size, step):
            print("%d done" % i)
            new_threshholds = []
            for j in range(0, max_size, step):
                scores = []
                for _ in range(iterations):
                    if i+1 < len(families_a) and j+1 < len(families_b):
                        i_fams = random.sample(families_a, i+1)
                        j_fams = random.sample(families_b, j+1)
                        scores.append(jaccard(i_fams, j_fams))
                    else:
                        # Cannot calculate threshold with these families, add 1
                        scores.append(1)

                # TODO (maybe?): cutoff is hard coded here, replace ?
                print(iterations, len(scores), scores)
                scores = sorted(scores)
                for _ in range(step):
                    new_threshholds.append(scores[int(iterations*0.95)])
            for _ in range(step):
                thresholds.append(new_threshholds)

        return thresholds


class ExpressionNetwork(db.Model):
    __tablename__ = 'expression_networks'
    id = db.Column(db.Integer, primary_key=True)
    probe = db.Column(db.String(50, collation=SQL_COLLATION), index=True)
    sequence_id = db.Column(db.Integer, db.ForeignKey('sequences.id', ondelete='CASCADE'), index=True)
    network = db.Column(db.Text)
    method_id = db.Column(db.Integer, db.ForeignKey('expression_network_methods.id', ondelete='CASCADE'), index=True)

    def __init__(self, probe, sequence_id, network, method_id):
        self.probe = probe
        self.sequence_id = sequence_id
        self.network = network
        self.method_id = method_id

    @property
    def neighbors_count(self):
        """
        Returns the number of neighors the current gene has

        :return: int, number of neighbors
        """
        data = json.loads(self.network)

        return len(data
