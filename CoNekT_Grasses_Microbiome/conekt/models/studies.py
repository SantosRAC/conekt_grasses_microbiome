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
    study_category = db.Column(db.Enum('ocean', 'agriculture', 'human', name='data_type'))

    def __init__(self, name, description,
                 data_type, study_category,
                 krona_html=None):
        self.name = name
        self.description = description
        self.data_type = data_type
        self.krona_html = krona_html
        self.study_category = study_category

    def __repr__(self):
        return str(self.id) + ". " + (f'{self.name}')
    
    def __str__(self):
        return str(self.id) + ". " + (f'{self.name}')
    
    @staticmethod
    def build_study(study_category, study_name, study_description,
                    study_type, krona_file):
        
        study_category = Species.query.get(study_category)

        new_study = Study(study_name, study_description, study_type, species.id, krona_file)        

        db.session.add(new_study)
        db.session.commit()
        
        return new_study.id