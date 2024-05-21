from conekt import db

from sqlalchemy.dialects.mysql import LONGTEXT

from flask import request, flash, url_for

from werkzeug.utils import redirect

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

from utils.parser.fasta import Fasta

import operator

from conekt.models.literature import LiteratureItem


class OperationalTaxonomicUnitMethod(db.Model):
    __tablename__ = 'otu_methods'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), index=True)
    clustering_method = db.Column(db.Enum('de_novo', 'closed_reference', 'open_reference', name='Clustering Method'), default='de_novo')
    clustering_threshold = db.Column(db.Float)
    clustering_algorithm = db.Column(db.Enum('vsearch', 'usearch', 'swarm', 'dada2', 'deblur', 'qiime1', name='Clustering Algorithm'), default='vsearch')
    clustering_reference_database = db.Column(db.String(255), default='')
    clustering_reference_db_release = db.Column(db.String(255), default='')
    amplicon_marker = db.Column(db.Enum('16S', 'ITS', name='sequence_type'), default='16S')
    primer_pair = db.Column(db.String(255), default='')
    literature_id = db.Column(db.Integer, db.ForeignKey('literature.id', ondelete='CASCADE'), index=True)

    def __init__(self, description, clustering_method, clustering_threshold,
                 clustering_algorithm, clustering_reference_database,
                 clustering_reference_db_release):
        self.description = description
        self.clustering_method = clustering_method
        self.clustering_threshold = clustering_threshold
        self.clustering_algorithm = clustering_algorithm
        self.clustering_reference_database = clustering_reference_database
        self.clustering_reference_db_release = clustering_reference_db_release
    
    def __repr__(self):
        return str(self.id) + ". " + self.id (self.clustering_method, self.clustering_algorithm)

class OperationalTaxonomicUnit(db.Model):
    __tablename__ = 'otus'
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.String(255), index=True)
    representative_sequence = db.deferred(db.Column(LONGTEXT))
    method_id = db.Column(db.Integer, db.ForeignKey('otu_methods.id', ondelete='CASCADE'), index=True)

    otus_profiles = db.relationship('OTUProfile', backref=db.backref('otu', lazy='joined'),
                                          lazy='dynamic',
                                          cascade="all, delete-orphan",
                                          passive_deletes=True)

    def __init__(self, original_id, representative_sequence, method_id):
        self.original_id = original_id
        self.representative_sequence = representative_sequence
        self.method_id = method_id
    
    def __repr__(self):
        return str(self.id) + ". " + self.method_id

    @staticmethod
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
                flash('Missing File. Reference-based methods (open or closed reference) require a reference database and release.', 'danger')
                return redirect(url_for('admin.add.otus.index'))

        fasta_data = Fasta()
        fasta_data.readfile(otus_fasta)

        literature_id = LiteratureItem.add(doi=literature_doi)

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

        db.session.add(new_otu_method)
        db.session.commit()

        added_otus = []
        new_otus = []

        # Loop over OTUs and add to db
        for name, sequence in sorted(fasta_data.sequences.items(), key=operator.itemgetter(0)):
            
            if name not in added_otus:
                added_otus.append(name)
            
            new_otu = OperationalTaxonomicUnit(**{"original_id": name,
                                              "representative_sequence": sequence,
                                              "method_id": new_otu_method.id})

            db.session.add(new_otu)
            new_otus.append(new_otu)

            # add 400 sequences at the time, more can cause problems with some database engines
            if len(new_otus) > 400:
                db.session.commit()
                new_otus = []

        # add the last set of sequences
        db.session.commit()

        return len(fasta_data.sequences.keys()), new_otu_method.id