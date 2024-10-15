from conekt import db
from conekt.models.relationships import sequence_go
from conekt.models.relationships.sequence_go import SequenceGOAssociation
from conekt.models.sequences import Sequence

from utils.parser.obo import Parser as OBOParser
from utils.parser.plaza.go import Parser as GOParser
from utils.enrichment import hypergeo_sf, fdr_correction

from collections import defaultdict

import json

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


# TODO: implement Solr search/indexing
class GO(db.Model):
    __tablename__ = 'go'
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50, collation=SQL_COLLATION), unique=True, index=True)
    name = db.Column(db.Text)
    type = db.Column(db.Enum('biological_process', 'molecular_function', 'cellular_component', name='go_type'))
    description = db.Column(db.Text)
    obsolete = db.Column(db.SmallInteger)
    is_a = db.Column(db.Text)
    extended_go = db.Column(db.Text)
    species_counts = db.Column(db.Text)

    sequences = db.relationship('Sequence', secondary=sequence_go, lazy='dynamic')

    def __init__(self, label, name, go_type, description, obsolete, is_a, extended_go):
        self.label = label
        self.name = name
        self.type = go_type
        self.description = description
        self.obsolete = obsolete
        self.is_a = is_a
        self.extended_go = extended_go
        self.species_counts = ""

    def set_all(self, label, name, go_type, description, extended_go):
        self.label = label
        self.name = name
        self.type = go_type
        self.description = description
        self.extended_go = extended_go
        self.species_counts = ""

    @property
    def short_type(self):
        if self.type == 'biological_process':
            return 'BP'
        elif self.type == 'molecular_function':
            return 'MF'
        elif self.type == 'cellular_component':
            return 'CC'
        else:
            return 'UNK'

    @property
    def readable_type(self):
        if self.type == 'biological_process':
            return 'Biological process'
        elif self.type == 'molecular_function':
            return 'Molecular function'
        elif self.type == 'cellular_component':
            return 'Cellular component'
        else:
            return 'Unknown type'

    @property
    def parent_count(self):
        """
        Returns total number of genes 'above' this gene in the DAG
        :return:
        """
        return len(self.extended_go.split(';')) if self.extended_go != '' else 0

    @property
    def interpro_stats(self):
        from conekt.models.interpro import Interpro

        return Interpro.sequence_stats_subquery(self.sequences)

    @property
    def go_stats(self):
        return GO.sequence_stats_subquery(self.sequences)

    @property
    def family_stats(self):
        from conekt.models.gene_families import GeneFamily

        return GeneFamily.sequence_stats_subquery(self.sequences)

    def species_occurrence(self, species_id):
        """
        count how many genes have the current GO term in a given species

        :param species_id: internal id of the selected species
        :return: count of sequences with this term associated
        """
        count = 0
        sequences = self.sequences.all()

        for s in sequences:
            if s.species_id == species_id:
                count += 1

        return count

    @staticmethod
    def sequence_stats(sequence_ids, exclude_predicted=True):
        """
        Takes a list of sequence IDs and returns InterPro stats for those sequences

        :param sequence_ids: list of sequence ids
        :param exclude_predicted: if True (default) predicted GO labels will be excluded
        :return: dict with for each InterPro domain linked with any of the input sequences stats
        """
        query = SequenceGOAssociation.query.filter(SequenceGOAssociation.sequence_id.in_(sequence_ids))

        if exclude_predicted:
            query = query.filter(SequenceGOAssociation.predicted == 0)

        data = query.all()

        return GO.__sequence_stats_associations(data)

    @staticmethod
    def sequence_stats_subquery(sequences, exclude_predicted=True):
        subquery = sequences.subquery()

        query = SequenceGOAssociation.query

        if exclude_predicted:
            query = query.filter(SequenceGOAssociation.predicted == 0)

        data = query.join(subquery, SequenceGOAssociation.sequence_id == subquery.c.id).all()

        return GO.__sequence_stats_associations(data)

    @staticmethod
    def __sequence_stats_associations(associations):
        output = {}
        for d in associations:
            if d.go_id not in output.keys():
                output[d.go_id] = {
                    'go': d.go,
                    'count': 1,
                    'sequences': [d.sequence_id],
                    'species': [d.sequence.species_id]
                }
            else:
                output[d.go_id]['count'] += 1
                if d.sequence_id not in output[d.go_id]['sequences']:
                    output[d.go_id]['sequences'].append(d.sequence_id)
                if d.sequence.species_id not in output[d.go_id]['species']:
                    output[d.go_id]['species'].append(d.sequence.species_id)

        for k, v in output.items():
            v['species_count'] = len(v['species'])
            v['sequence_count'] = len(v['sequences'])

        return output

    @staticmethod
    def update_species_counts():
        """
        Adds phylo-profile to each go-label, results are stored in the database

        :param exclude_predicted: if True (default) predicted GO labels will be excluded
        """
        # link species to sequences
        sequences = db.session.execute(db.select(Sequence.id, Sequence.species_id)).all()

        sequence_to_species = {}
        for seq_id, species_id in sequences:
            if species_id is not None:
                sequence_to_species[seq_id] = int(species_id)

        # get go for all genes
        associations = db.session.execute(
            db.select(SequenceGOAssociation.sequence_id, SequenceGOAssociation.go_id).distinct().
            where(SequenceGOAssociation.predicted == 0)).all()

        count = {}
        for seq_id, go_id in associations:
            species_id = sequence_to_species[seq_id]

            if go_id not in count.keys():
                count[go_id] = {}

            if species_id not in count[go_id]:
                count[go_id][species_id] = 1
            else:
                count[go_id][species_id] += 1

        # update counts
        for go_id, data in count.items():
            db.session.execute(db.update(GO.__table__)
                              .where(GO.__table__.c.id == go_id)
                              .values(species_counts=json.dumps(data)))

    @staticmethod
    def add_from_obo(filename, empty=True, compressed=False):
        """
        Parses GeneOntology's OBO file and adds it to the database

        :param filename: Path to the OBO file to parse
        :param compressed: load data from .gz file if true (default: False)
        :param empty: Empty the database first when true (default: True)
        """
        # If required empty the table first
        if empty:
            try:
                db.session.query(GO).delete()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)

        obo_parser = OBOParser()
        obo_parser.readfile(filename, compressed=compressed)

        obo_parser.extend_go()

        for i, term in enumerate(obo_parser.terms):
            go = GO(term.id, term.name, term.namespace, term.definition, term.is_obsolete, ";".join(term.is_a),
                    ";".join(term.extended_go))

            db.session.add(go)

            if i % 40 == 0:
                # commit to the db frequently to allow WHOOSHEE's indexing function to work without timing out
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(e)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)

    @staticmethod
    def add_go_from_plaza(filename):
        """
        Adds GO annotation from PLAZA 3.0 to the database

        :param filename: Path to the annotation file
        :return:
        """
        go_parser = GOParser()

        go_parser.read_plaza_go(filename)

        gene_hash = {}
        go_hash = {}

        all_sequences = Sequence.query.all()
        all_go = GO.query.all()

        for sequence in all_sequences:
            gene_hash[sequence.name] = sequence

        for term in all_go:
            go_hash[term.label] = term

        associations = []

        for gene, terms in go_parser.annotation.items():
            if gene in gene_hash.keys():
                current_sequence = gene_hash[gene]
                for term in terms:
                    if term["id"] in go_hash.keys():
                        current_term = go_hash[term["id"]]
                        association = SequenceGOAssociation(**{"sequence_id": current_sequence.id,
                            "go_id": current_term.id,
                            "evidence": term["evidence"],
                            "source": term["source"]})
                        associations.append(association)
                    else:
                        print(term, "not found in the database.")
            else:
                print("Gene", gene, "not found in the database.")

            if len(associations) > 400:
                db.session.add_all(associations)
                db.session.commit()
                associations = []
        
        db.session.add_all(associations)
        db.session.commit()

        # Add extended GOs
        for gene, terms in go_parser.annotation.items():
            if gene in gene_hash.keys():
                current_sequence = gene_hash[gene]
                new_terms = []
                current_terms = []

                for term in terms:
                    if term["id"] not in current_terms:
                        current_terms.append(term["id"])

                for term in terms:
                    if term["id"] in go_hash.keys():
                        extended_terms = go_hash[term["id"]].extended_go.split(";")
                        for extended_term in extended_terms:
                            if extended_term not in current_terms and extended_term not in new_terms:
                                new_terms.append(extended_term)

                for new_term in new_terms:
                    if new_term in go_hash.keys():
                        current_term = go_hash[new_term]
                        association = SequenceGOAssociation(**{"sequence_id": current_sequence.id,
                            "go_id": current_term.id,
                            "evidence": None,
                            "source": "Extended"})
                        associations.append(association)

                    if len(associations) > 400:
                        db.session.add_all(associations)
                        db.session.commit()
                        associations = []

        db.session.add_all(associations)
        db.session.commit()

    @staticmethod
    def add_go_from_tab(filename, species_id, source="Source not provided"):
        gene_hash = {}
        go_hash = {}

        all_sequences = Sequence.query.filter(Sequence.species_id == species_id, Sequence.type == 'protein_coding').all()
        all_go = GO.query.all()

        for sequence in all_sequences:
            gene_hash[sequence.name] = sequence

        for term in all_go:
            go_hash[term.label] = term

        associations = []

        gene_go = defaultdict(list)

        with open(filename, "r") as f:
            for line in f:
                gene, term, evidence = line.strip().split('\t')
                if gene in gene_hash.keys():
                    current_sequence = gene_hash[gene]
                    if term in go_hash.keys():
                        current_term = go_hash[term]
                        association = SequenceGOAssociation(**{"sequence_id": current_sequence.id,
                            "go_id": current_term.id,
                            "evidence": evidence,
                            "source": source})
                        associations.append(association)

                        if term not in gene_go[gene]:
                            gene_go[gene].append(term)
                            db.session.add(association)

                    else:
                        print(term, "not found in the database.")
                else:
                    print("Gene", gene, "not found in the database.")

                if len(associations) > 400:
                    db.session.commit()
                    associations = []

        db.session.commit()

        # Add extended GOs
        for gene, terms in gene_go.items():
            if gene in gene_hash.keys():
                current_sequence = gene_hash[gene]
                new_terms = []
                current_terms = []

                for term in terms:
                    if term not in current_terms:
                        current_terms.append(term)

                for term in terms:
                    if term in go_hash.keys():
                        extended_terms = go_hash[term].extended_go.split(";")
                        for extended_term in extended_terms:
                            if extended_term not in current_terms and extended_term not in new_terms:
                                new_terms.append(extended_term)

                for new_term in new_terms:
                    if new_term in go_hash.keys():
                        current_term = go_hash[new_term]
                        association = SequenceGOAssociation(**{"sequence_id": current_sequence.id,
                            "go_id": current_term.id,
                            "evidence": None,
                            "source": "Extended"})
                        associations.append(association)
                        db.session.add(association)

                    if len(associations) > 400:
                        db.session.commit()
                        associations = []

        db.session.commit()