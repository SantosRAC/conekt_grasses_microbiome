from conekt import db

from conekt.models.relationships import sequence_go, sequence_interpro, sequence_cazyme, sequence_family
from conekt.models.relationships import sequence_xref
from utils.sequence import translate
from utils.parser.fasta import Fasta

from sqlalchemy.orm import undefer
from sqlalchemy.dialects.mysql import LONGTEXT
import operator
import sys

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


# TODO: add decorator for Solr
class Sequence(db.Model):
    __tablename__ = 'sequences'
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id', ondelete='CASCADE'), index=True)
    name = db.Column(db.String(80, collation=SQL_COLLATION), index=True)
    description = db.Column(db.Text)
    coding_sequence = db.deferred(db.Column(LONGTEXT))
    type = db.Column(db.Enum('protein_coding', 'TE', 'RNA', name='sequence_type'), default='protein_coding')
    is_mitochondrial = db.Column(db.SmallInteger, default=False)
    is_chloroplast = db.Column(db.SmallInteger, default=False)

    expression_profiles = db.relationship('ExpressionProfile', backref=db.backref('sequence', lazy='joined'),
                                          lazy='dynamic',
                                          cascade="all, delete-orphan",
                                          passive_deletes=True)

    # Other properties
    #
    # coexpression_cluster_associations declared in 'SequenceCoexpressionClusterAssociation'
    # interpro_associations declared in 'SequenceInterproAssociation'
    # go_associations declared in 'SequenceGOAssociation'
    # cazyme_associations declared in 'SequenceCAZYmeAssociation'
    # family_associations declared in 'SequenceFamilyAssociation'

    go_labels = db.relationship('GO', secondary=sequence_go, lazy='dynamic')
    interpro_domains = db.relationship('Interpro', secondary=sequence_interpro, lazy='dynamic')
    cazymes = db.relationship('CAZYme', secondary=sequence_cazyme, lazy='dynamic')
    families = db.relationship('GeneFamily', secondary=sequence_family, lazy='dynamic')

    clade_associations_one = db.relationship('SequenceSequenceCladeAssociation',
                                             primaryjoin="SequenceSequenceCladeAssociation.sequence_one_id == Sequence.id",
                                             backref=db.backref('sequence_one', lazy='joined'),
                                             lazy='dynamic')

    clade_associations_two = db.relationship('SequenceSequenceCladeAssociation',
                                             primaryjoin="SequenceSequenceCladeAssociation.sequence_two_id == Sequence.id",
                                             backref=db.backref('sequence_two', lazy='joined'),
                                             lazy='dynamic')

    xrefs = db.relationship('XRef', secondary=sequence_xref, lazy='joined')

    def __init__(self, species_id, name, coding_sequence, type='protein_coding', is_chloroplast=False,
                 is_mitochondrial=False, description=None):
        self.species_id = species_id
        self.name = name
        self.description = description
        self.coding_sequence = coding_sequence
        self.type = type
        self.is_chloroplast = is_chloroplast
        self.is_mitochondrial = is_mitochondrial

    @property
    def protein_sequence(self):
        """
        Function to translate the coding sequence to the amino acid sequence. Will start at the first start codon and
        break after adding a stop codon (indicated by '*')

        :return: The amino acid sequence based on the coding sequence
        """
        return translate(self.coding_sequence)

    @property
    def aliases(self):
        """
        Returns a readable string with the aliases or tokens stored for this sequence in the table xrefs

        :return: human readable string with aliases or None
        """
        t = [x.name for x in self.xrefs if x.platform == 'token']

        return ", ".join(t) if len(t) > 0 else None

    @property
    def shortest_alias(self):
        """
        Returns the shortest alias

        :return: string with shortest alias or None (in case no aliases exist)
        """
        t = [x.name for x in self.xrefs if x.platform == 'token']

        return min(t, key=len) if len(t) > 0 else None

    @property
    def display_name(self):
        """
        Returns a name to display (from xrefs with display) if available otherwise return name

        :return: display name
        """
        t = [x.name for x in self.xrefs if x.platform == 'display']

        return t[0] if len(t) > 0 else self.name

    @property
    def best_name(self):
        """
        Checks if there is a display name, if not checks the shortest alias, otherwise returns name. To be used in e.g.
        graphs

        :return: string with best name to show in graphs, ...
        """
        if self.display_name is not self.name:
            return self.display_name
        elif self.shortest_alias is not None:
            return self.shortest_alias
        else:
            return self.name

    @property
    def readable_type(self):
        """
        Converts the type table to a readable string

        :return: string with readable version of the sequence type
        """
        conversion = {'protein_coding': 'protein coding',
                      'TE': 'transposable element',
                      'RNA': 'RNA'}

        if self.type in conversion.keys():
            return conversion[self.type]
        else:
            return 'other'

    @staticmethod
    def add_from_fasta(filename, species_id, compressed=False, sequence_type='protein_coding'):
        fasta_data = Fasta()
        fasta_data.readfile(filename, compressed=compressed)

        new_sequences = []

        # Loop over sequences, sorted by name (key here) and add to db
        for name, sequence in sorted(fasta_data.sequences.items(), key=operator.itemgetter(0)):
            new_sequence = Sequence(**{"species_id": species_id,
                            "name": name,
                            "description": None,
                            "coding_sequence": sequence,
                            "type": sequence_type,
                            "is_mitochondrial": False,
                            "is_chloroplast": False})

            new_sequences.append(new_sequence)

            # add 400 sequences at the time, more can cause problems with some database engines
            if len(new_sequences) > 400:
                db.session.add_all(new_sequences)
                db.session.commit()
                new_sequences = []

        # add the last set of sequences
        db.session.add_all(new_sequences)
        db.session.commit()

        return len(fasta_data.sequences.keys())

    @staticmethod
    def add_descriptions(filename, species_id):
        sequences = Sequence.query.filter_by(species_id=species_id, type='protein_coding').all()

        seq_dict = {}

        for s in sequences:
            seq_dict[s.name] = s

        with open(filename, "r") as f_in:
            for i, line in enumerate(f_in):
                try:
                    name, description = line.strip().split('\t')
                except ValueError:
                    print("Cannot parse line %d: \"%s\"" % (i, line), file=sys.stderr)
                finally:
                    if name in seq_dict.keys():
                        seq_dict[name].description = description

                if i % 400 == 0:
                    db.session.commit()

            db.session.commit()

    @staticmethod
    def export_cds(filename):
        sequences = Sequence.query.options(undefer('coding_sequence')).all()

        with open(filename, "w") as f_out:
            for s in sequences:
                print(">%s\n%s" % (s.name, s.coding_sequence), file=f_out)

    @staticmethod
    def export_protein(filename):
        sequences = Sequence.query.options(undefer('coding_sequence')).all()

        with open(filename, "w") as f_out:
            for s in sequences:
                print(">%s\n%s" % (s.name, s.protein_sequence), file=f_out)
