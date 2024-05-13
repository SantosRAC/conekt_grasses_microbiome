from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

from conekt.models.taxonomy import SILVATaxon
from conekt.models.microbiome.asvs import AmpliconSequenceVariant

from flask import flash, url_for

class ASVClassificationMethod(db.Model):
    __tablename__ = 'asv_classification_methods'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    classifier_name = db.Column(db.Enum('classify-sklearn', 'other', name=''),
                                default='classify-sklearn')
    classifier_version = db.Column(db.String(255), default='')
    ref_database = db.Column(db.String(255), default='silva')
    ref_db_release = db.Column(db.String(255), default='')

    def __init__(self, description, classifier_name,
                 classifier_version, ref_database,
                 ref_db_release):
        self.description = description
        self.classifier_name = classifier_name
        self.classifier_version = classifier_version
        self.ref_database = ref_database
        self.ref_db_release = ref_db_release
    
    def __repr__(self):
        return str(self.id) + ". " + self.classifier_name + " " + self.classifier_version



class ASVClassification(db.Model):
    __tablename__ = 'asv_classification'
    id = db.Column(db.Integer, primary_key=True)
    asv_id = db.Column(db.Integer, db.ForeignKey('asvs.id', ondelete='CASCADE'), index=True)
    silva_id = db.Column(db.Integer, db.ForeignKey('silva_taxonomy.id', ondelete='CASCADE'), index=True)
    method_id = db.Column(db.Integer, db.ForeignKey('asv_classification_methods.id', ondelete='CASCADE'), index=True)

    def __init__(self, asv_id, silva_id, method_id):
        self.asv_id = asv_id
        self.silva_id = silva_id
        self.method_id = method_id
    
    def __repr__(self):
        return str(self.id) + ". " + self.asv_id + " " + self.silva_id
    
    @staticmethod
    def add_asv_classification_from_table(asv_classification_table,
                                    asv_classification_description,
                                    classifier_name,
                                    classifier_version,
                                    ref_db_release):
        """
        Function to add ASV classification to the database

        :param asv_classification_table: path to the file with ASV classification
        :param asv_classification_description: description of the ASV classification method
        :param asv_classification_method: method used to classify the ASVs
        :param classifier_version: version of the classifier used
        :param ref_db_release: release of the reference database used
        """
        
        new_classification_method = ASVClassificationMethod(asv_classification_description,
                                    classifier_name, classifier_version,
                                    'silva', ref_db_release)
        
        db.session.add(new_classification_method)
        db.session.commit()

        classified_asvs = 0
        new_asv_classifications = []

        with open(asv_classification_table, 'r') as fin:

            _ = fin.readline()

            for line in fin:
                parts = line.strip().split('\t')

                if len(parts) == 2:

                    asv_name, silva_path = parts

                    asv_record = AmpliconSequenceVariant.query.filter_by(original_id=asv_name).first()

                    silva_record = SILVATaxon.query.filter_by(taxon=silva_path).first()

                    new_asv_classification = ASVClassification(asv_record.id, silva_record.id, new_classification_method.id)

                    db.session.add(new_asv_classification)
                    classified_asvs+=1
                    new_asv_classifications.append(new_asv_classification)

                    if len(new_asv_classifications) > 400:
                        db.session.commit()
                        new_asv_classifications = []

            db.session.commit()
        
        return classified_asvs