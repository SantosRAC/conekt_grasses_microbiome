from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

from conekt.models.species import Species
from conekt.models.seq_run import SeqRun
from conekt.models.relationships.study_literature import StudyLiteratureAssociation
from conekt.models.relationships.study_sample import StudySampleAssociation
from conekt.models.relationships.study_run import StudyRunAssociation

from sqlalchemy.dialects.mysql import LONGTEXT

class Study(db.Model):
    __tablename__ = 'studies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255, collation=SQL_COLLATION))
    description = db.Column(db.Text)
    data_type = db.Column(db.Enum('metataxonomics', 'expression_metataxonomics', name='data_type'))
    krona_html = db.deferred(db.Column(LONGTEXT))
    species_id = db.Column(db.Integer, db.ForeignKey('species.id', ondelete='CASCADE'), index=True)

    def __init__(self, name, description,
                 data_type, species_id,
                 krona_html=None):
        self.name = name
        self.description = description
        self.data_type = data_type
        self.krona_html = krona_html
        self.species_id = species_id

    def __repr__(self):
        return str(self.id) + ". " + (f'{self.name}')
    
    def __str__(self):
        return str(self.id) + ". " + (f'{self.name}')
    
    @staticmethod
    def build_study(species_id, study_name, study_description,
                    study_type, literature_ids, krona_file):
        
        species = Species.query.get(species_id)

        new_study = Study(study_name, study_description, study_type, species.id, krona_file)        

        db.session.add(new_study)
        db.session.commit()

        associated_literature = 0
        associated_samples = 0

        if study_type == 'metataxonomics':

            for lit_id in literature_ids:

                literature_metatax_runs = SeqRun.query.filter_by(species_id=species.id, data_type='metataxonomics', literature_id=lit_id).all()

                new_study_lit = StudyLiteratureAssociation(new_study.id, lit_id)
                db.session.add(new_study_lit)

                for run in literature_metatax_runs:

                    new_study_run = StudyRunAssociation(new_study.id, run.id, 'metataxonomics') 
                    db.session.add(new_study_run)

                    new_study_sample = StudySampleAssociation(new_study.id, run.sample_id) 
                    db.session.add(new_study_sample)

            db.session.commit()
                
        else:

            samples_rnaseq_runs = []
            samples_metatax_runs = []
            rnaseq_runs = []
            metatax_runs = []

            for lit_id in literature_ids:
                
                rnaseq_runs = SeqRun.query.filter_by(species_id=species.id, data_type='rnaseq', literature_id=lit_id).all()
                metatax_runs = SeqRun.query.filter_by(species_id=species.id, data_type='metataxonomics', literature_id=lit_id).all()

                samples_rnaseq_runs.extend([run.sample_id for run in rnaseq_runs])
                samples_metatax_runs.extend([run.sample_id for run in metatax_runs])

            sample_intersection = set(samples_rnaseq_runs).intersection(set(samples_metatax_runs))

            if list(sample_intersection).sort() == samples_rnaseq_runs.sort():

                for sample_id in sample_intersection:
                    new_study_sample = StudySampleAssociation(new_study.id, sample_id)
                    db.session.add(new_study_sample)

                    associated_samples+=1
                
                for lit_id in literature_ids:
                    new_study_lit = StudyLiteratureAssociation(new_study.id, lit_id)
                    db.session.add(new_study_lit)

                    associated_literature+=1

                for run in rnaseq_runs:
                    new_study_run = StudyRunAssociation(new_study.id, run.id, data_type='rnaseq')
                    db.session.add(new_study_run)

                for run in metatax_runs:
                    new_study_run = StudyRunAssociation(new_study.id, run.id, data_type='metataxonomics')
                    db.session.add(new_study_run)
                
                db.session.commit()               

        
        return associated_literature, associated_samples