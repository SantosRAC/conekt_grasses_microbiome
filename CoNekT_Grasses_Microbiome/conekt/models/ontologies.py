from conekt import db

from conekt.models.sample import Sample
from conekt.models.relationships.sample_po import SamplePOAssociation
from conekt.models.relationships.sample_peco import SamplePECOAssociation
from conekt.models.relationships.sample_envo import SampleENVOAssociation

import os

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class PlantOntology(db.Model):
    __tablename__ = 'plant_ontology'
    id = db.Column(db.Integer, primary_key=True)
    po_term = db.Column(db.String(10, collation=SQL_COLLATION), unique=True)
    po_class = db.Column(db.String(50, collation=SQL_COLLATION), unique=True)
    po_annotation = db.Column(db.String(500, collation=SQL_COLLATION))

    def __init__(self, po_term, po_class, po_annotation):
        self.po_term = po_term
        self.po_class = po_class
        self.po_annotation = po_annotation

    def __repr__(self):
        return str(self.id) + ". " + self.po_term
    
    @staticmethod
    def add_tabular_po(filename, empty=True):

        # If required empty the table first

        file_size = os.stat(filename).st_size
        if empty and file_size > 0:
            try:
                db.session.query(PlantOntology).delete()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)
    
        with open(filename, 'r') as fin:
            i = 0
            for line in fin:
                if line.startswith('PO:'):
                    parts = line.strip().split('\t')
                    if len(parts) == 6:
                        po_id, po_name, po_defn = parts[0], parts[1], parts[2]
                        po = PlantOntology(po_term=po_id, po_class=po_name, po_annotation=po_defn)
                        db.session.add(po)
                        i += 1
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
    def add_sample_po_association(sample_id, po_term):

        sample = Sample.query.get(sample_id)
        po = PlantOntology.query.filter_by(po_term=po_term).first()
        species_id = sample.species_id
        
        association = {'sample_id': sample.id,
                       'po_id': po.id,
                       'species_id': species_id}
    
        db.session.execute(SamplePOAssociation.__table__.insert(), association)


class PlantExperimentalConditionsOntology(db.Model):
    __tablename__ = 'plant_experimental_conditions_ontology'
    id = db.Column(db.Integer, primary_key=True)
    peco_term = db.Column(db.String(13, collation=SQL_COLLATION), unique=True)
    peco_class = db.Column(db.String(50, collation=SQL_COLLATION), unique=True)
    peco_annotation = db.Column(db.String(500, collation=SQL_COLLATION))

    def __init__(self, peco_term, peco_class, peco_annotation):
        self.peco_term = peco_term
        self.peco_class = peco_class
        self.peco_annotation = peco_annotation

    def __repr__(self):
        return str(self.id) + ". " + self.peco_term
    
    @staticmethod
    def add_tabular_peco(filename, empty=True):

        # If required empty the table first

        file_size = os.stat(filename).st_size
        if empty and file_size > 0:
            try:
                db.session.query(PlantExperimentalConditionsOntology).delete()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)

        with open(filename, 'r') as fin:
            i = 0
            for line in fin:
                if line.startswith('PECO:'):
                    parts = line.strip().split('\t')
                    if len(parts) == 3:
                        peco_id, peco_name, peco_defn = parts[0], parts[1], parts[2]
                        print("'",peco_id,"'")
                        peco = PlantExperimentalConditionsOntology(peco_term=peco_id, peco_class=peco_name, peco_annotation=peco_defn)
                        db.session.add(peco)
                        i += 1
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
    def add_sample_peco_association(sample_id, peco_term):

        sample = Sample.query.get(sample_id)
        peco = PlantExperimentalConditionsOntology.query.filter_by(peco_term=peco_term).first()
        species_id = sample.species_id

        association = {'sample_id': sample.id,
                       'peco_id': peco.id,
                       'species_id': species_id}
    
        db.session.execute(SamplePECOAssociation.__table__.insert(), association)


class EnvironmentOntology(db.Model):
    __tablename__ = 'environment_ontology'
    id = db.Column(db.Integer, primary_key=True)
    envo_term = db.Column(db.String(13, collation=SQL_COLLATION), unique=True)
    envo_class = db.Column(db.String(50, collation=SQL_COLLATION), unique=True)
    envo_annotation = db.Column(db.String(500, collation=SQL_COLLATION))

    def __init__(self, envo_term, envo_class, envo_annotation):
        self.envo_term = envo_term
        self.envo_class = envo_class
        self.envo_annotation = envo_annotation

    def __repr__(self):
        return str(self.id) + ". " + self.envo_term
    
    @staticmethod
    def add_tabular_envo(filename, empty=True):

        # If required empty the table first
        file_size = os.stat(filename).st_size
        if empty and file_size > 0:
            try:
                db.session.query(EnvironmentOntology).delete()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)

        with open(filename, 'r') as fin:
            i = 0
            for line in fin:
                if line.startswith('ENVO:'):
                    parts = line.strip().split('\t')
                    if len(parts) == 3:
                        envo_term, envo_name, envo_annotation = parts[0], parts[1], parts[2]
                        envo = EnvironmentOntology(envo_term=envo_term,
                                envo_class=envo_name,
                                envo_annotation=envo_annotation)
                        db.session.add(envo)
                        i += 1
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
    def add_sample_envo_association(sample_id, envo_term):

        sample = Sample.query.get(sample_id)
        envo = EnvironmentOntology.query.filter_by(envo_term=envo_term).first()
        species_id = sample.species_id

        association = {'sample_id': sample.id,
                       'envo_id': envo.id,
                       'species_id': species_id}
    
        db.session.execute(SampleENVOAssociation.__table__.insert(), association)


class OntologyHostMicrobeInteraction(db.Model):
    __tablename__ = 'ohmi'
    id = db.Column(db.Integer, primary_key=True)
    ohmi_term = db.Column(db.String(10, collation=SQL_COLLATION), unique=True)
    ohmi_class = db.Column(db.String(50, collation=SQL_COLLATION), unique=True)
    ohmi_annotation = db.Column(db.String(500, collation=SQL_COLLATION))

    def __init__(self, ohmi_term, ohmi_class, ohmi_annotation):
        self.ohmi_term = ohmi_term
        self.ohmi_class = ohmi_class
        self.ohmi_annotation = ohmi_annotation

    def __repr__(self):
        return str(self.id) + ". " + self.ohmi_term