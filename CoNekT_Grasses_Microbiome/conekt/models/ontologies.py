from conekt import db, whooshee

from conekt.models.sample import Sample
from conekt.models.relationships.sample_envo import SampleENVOAssociation

import os

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

@whooshee.register_model('id', 'envo_term', 'envo_class', 'envo_annotation')
class EnvironmentOntology(db.Model):
    __tablename__ = 'environment_ontology'
    id = db.Column(db.Integer, primary_key=True)
    envo_term = db.Column(db.String(13, collation=SQL_COLLATION), unique=True)
    envo_class = db.Column(db.String(500, collation=SQL_COLLATION), unique=True)
    envo_annotation = db.Column(db.String(500, collation=SQL_COLLATION))

    def __init__(self, envo_term, envo_class, envo_annotation):
        self.envo_term = envo_term
        self.envo_class = envo_class
        self.envo_annotation = envo_annotation

    def __repr__(self):
        return str(self.id) + ". " + self.envo_term
    
    @staticmethod
    def add_tabular_envo(filename, empty=True):

        # # If required empty the table first
        # file_size = os.stat(filename).st_size
        # if empty and file_size > 0:
        #     try:
        #         db.session.query(EnvironmentOntology).delete()
        #         db.session.commit()
        #     except Exception as e:
        #         db.session.rollback()
        #         print(e)

        with open(filename, 'r') as file:
           # get rid of the header
            _ = file.readline()

            lines = file.readlines()

            for line in lines:
                #split the line into the ENVO informations
                parts = line.strip().split('\t')
                envo_term = parts[0]
                envo_name = parts[1]
                envo_annotation = parts[2]

                envo_ontology = EnvironmentOntology(envo_term, envo_name, envo_annotation)
                db.session.add(envo_ontology) 
                db.session.commit()    
    
    @staticmethod
    def add_sample_envo_association(sample_id, envo_term):

        sample = Sample.query.get(sample_id)
        envo = EnvironmentOntology.query.filter_by(envo_term=envo_term).first()
        species_id = sample.species_id

        association = {'sample_id': sample.id,
                       'envo_id': envo.id,
                       'species_id': species_id}
    
        db.session.execute(SampleENVOAssociation.__table__.insert(), association)