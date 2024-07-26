from conekt import db

from flask import request, flash, url_for

from conekt.models.sample import Sample
from conekt.models.literature import LiteratureItem

from conekt.models.relationships.study_run import StudyRunAssociation
from conekt.models.relationships.study_sample import StudySampleAssociation
from conekt.models.relationships.study_literature import StudyLiteratureAssociation

from sqlalchemy.orm import undefer

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

class SeqRun(db.Model):
    __tablename__ = 'sequencing_runs'
    id = db.Column(db.Integer, primary_key=True)
    accession_number = db.Column(db.String(50, collation=SQL_COLLATION), unique=True)
    seq_platform = db.Column(db.Enum('illumina', 'pacbio', 'nanopore', name='Sequencing Platform'), default='illumina')
    strandness = db.Column(db.Enum('unstranded', 'strand specific', name='RNA-Seq layout'), default='unstranded')
    layout = db.Column(db.Enum('paired-end', 'single-end', name='RNA-Seq layout'), default='single-end')
    data_type = db.Column(db.Enum('rnaseq', 'metataxonomics', name='data_type'))
    species_id = db.Column(db.Integer, db.ForeignKey('species.id', ondelete='CASCADE'), index=True)
    sample_id = db.Column(db.Integer, db.ForeignKey('samples.id', ondelete='CASCADE'), index=True)
    literature_id = db.Column(db.Integer, db.ForeignKey('literature.id', ondelete='CASCADE'), index=True)

    def __init__(self, accession_number, sample_id, literature_id,
                 seq_platform, species_id, strandness = 'unstranded',
                 data_type = 'rnaseq', layout = 'paired-end'):
        self.accession_number = accession_number
        self.layout = layout
        self.sample_id = sample_id
        self.literature_id = literature_id
        self.seq_platform = seq_platform
        self.species_id = species_id
        self.strandness = strandness
        self.data_type = data_type
    
    def __repr__(self):
        return str(self.id) + ". " + self.accession_number

    @staticmethod
    def add_run_annotation(run_annotation_file, species_id, data_type,
                           study_id=None):
        """Function to add run information to the database from annotation file

        :param run_annotation_file: path to the file with runs and their metatada
        :param species_id: internal id of the species
        :param data_type: type of data (rnaseq or metataxonomics)
        :param study_id: internal id of the study (optional)
        """

        with open(run_annotation_file, 'r') as fin:
            # get rid of the header
            _ = fin.readline()

            added_runs = 0
            all_new_runs = []
            new_runs = []

            for line in fin:
                parts = line.strip().split('\t')
                
                if len(parts) == 6:
                    run_name = parts[0]
                    sample_name = parts[1]
                    doi = parts[2]
                    seq_strandness = parts[3]
                    seq_layout = parts[4]
                    seq_platform = parts[5]

                    sample = Sample.query.filter_by(name=sample_name).\
                        filter_by(species_id=species_id).\
                        first()
                    
                    literature = LiteratureItem.query.filter_by(doi=doi).first()

                    if literature:
                        literature_id = literature.id
                    else:
                        literature_id = LiteratureItem.add(doi)
                    
                    new_run = SeqRun(run_name, sample.id, literature_id,
                                     seq_platform, species_id, seq_strandness,
                                     data_type, seq_layout)

                    db.session.add(new_run)
                    added_runs+=1
                    new_runs.append(new_run)
                    all_new_runs.append(new_run)

                    if study_id:
                        new_study_sample = StudySampleAssociation(study_id, sample.id)
                        db.session.add(new_study_sample)
                        new_study_literature = StudyLiteratureAssociation(study_id, literature_id)
                        db.session.add(new_study_literature)

                    if len(new_runs) > 400:
                        db.session.commit()
                        new_runs = []
        
            db.session.commit()

            if study_id:
                for run in all_new_runs:
                    new_study_run = StudyRunAssociation(study_id, run.id, 'metataxonomics')
                    db.session.add(new_study_run)
            
            db.session.commit()

        return added_runs

            



