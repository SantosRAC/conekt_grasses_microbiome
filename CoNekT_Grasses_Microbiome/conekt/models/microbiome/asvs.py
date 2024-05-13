from conekt import db

from sqlalchemy.dialects.mysql import LONGTEXT

from utils.parser.fasta import Fasta

import operator

from conekt.models.literature import LiteratureItem

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

class AmpliconSequenceVariantMethod(db.Model):
    """
    
    name: name of the ASV method
    description: description of the ASV method
    method: method used to generate ASVs (e.g., dada2, deblur)
    amplicon_marker: marker used to generate ASVs (e.g., 16S, ITS)
    primer_pair: primer pair used to generate amplicon
    """
    __tablename__ = 'asv_methods'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    name = db.Column(db.Enum('dada2', 'deblur', name='data_type'), default='dada2')
    amplicon_marker = db.Column(db.Enum('16S', 'ITS', name='sequence_type'), default='16S')
    primer_pair = db.Column(db.String(255), default='')
    literature_id = db.Column(db.Integer, db.ForeignKey('literature.id', ondelete='CASCADE'), index=True)


    def __init__(self, description, name,
                 amplicon_marker, primer_pair,
                 literature_id):
        self.description = description
        self.name = name
        self.amplicon_marker = amplicon_marker
        self.primer_pair = primer_pair
        self.literature_id = literature_id
    
    def __repr__(self):
        return str(self.id) + ". " + self.description


class AmpliconSequenceVariant(db.Model):
    __tablename__ = 'asvs'
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.String(255, collation=SQL_COLLATION),
                            nullable=False, unique=True, index=True)
    representative_sequence = db.deferred(db.Column(LONGTEXT))

    method_id = db.Column(db.Integer, db.ForeignKey('asv_methods.id', ondelete='CASCADE'), index=True)

    asvs_profiles = db.relationship('ASVProfile', backref=db.backref('asv', lazy='joined'),
                                          lazy='dynamic',
                                          cascade="all, delete-orphan",
                                          passive_deletes=True)

    def __init__(self, original_id, representative_sequence,
                 method_id):
        self.original_id = original_id
        self.representative_sequence = representative_sequence
        self.method_id = method_id
    
    def __repr__(self):
        return str(self.id) + ". " + self.original_id

    @staticmethod
    def add_asvs_from_fasta(asvs_fasta,
                 asv_method_description,
                 asv_source_method,
                 amplicon_marker,
                 primer_pair, literature_doi):
        """
        Function to add ASV to the database

        :param asvs_fasta: path to the file with runs and their metatada
        :param asv_method_description: description of the ASV method
        :param asv_source_method: currently dada2 or deblur
        :param amplicon_marker: marker (currently 16S or ITS)
        :param primer_pair: primer pair used to generate amplicons
        :param literature_doi: DOI of the publication describing the method
        """

        fasta_data = Fasta()
        fasta_data.readfile(asvs_fasta)

        literature_id = LiteratureItem.add(doi=literature_doi)

        # Add ASV method
        new_asv_method = AmpliconSequenceVariantMethod(**{"description": asv_method_description,
                                                     "name": asv_source_method,
                                                     "amplicon_marker": amplicon_marker,
                                                     "primer_pair": primer_pair,
                                                     "literature_id": literature_id})

        db.session.add(new_asv_method)
        db.session.commit()

        added_asvs = []
        new_asvs = []

        # Loop over asvs and add to db
        for name, sequence in sorted(fasta_data.sequences.items(), key=operator.itemgetter(0)):
            
            if name not in added_asvs:
                added_asvs.append(name)            
            
            new_asv = AmpliconSequenceVariant(**{"original_id": name,
                                              "representative_sequence": sequence,
                                              "method_id": new_asv_method.id})

            db.session.add(new_asv)
            new_asvs.append(new_asv)

            # add 400 sequences at the time, more can cause problems with some database engines
            if len(new_asvs) > 400:
                db.session.commit()
                new_asvs = []

        # add the last set of sequences
        db.session.commit()

        return len(fasta_data.sequences.keys()), new_asv_method.id