from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

from conekt.models.taxonomy import GGTaxon, SILVATaxon
from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit

class OTUClassificationMethod(db.Model):
    __tablename__ = 'otu_classification_methods'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    classifier_name = db.Column(db.Enum('uclust', 'other', name=''),
                                default='uclust')
    classifier_version = db.Column(db.String(255), default='')
    classification_ref_db = db.Column(db.Enum('greengenes', 'silva', 'other', name=''),
                             default='silva')
    classification_ref_db_release = db.Column(db.String(255), default='')

    def __init__(self, description, classifier_name,
                 classifier_version, classification_ref_db,
                 classification_ref_db_release):
        self.description = description
        self.classifier_name = classifier_name
        self.classifier_version = classifier_version
        self.classification_ref_db = classification_ref_db
        self.classification_ref_db_release = classification_ref_db_release
    
    def __repr__(self):
        return str(self.id) + ". " + self.classifier_name + " " + self.classifier_version


class OTUClassification(db.Model):
    __tablename__ = 'otu_classification'
    id = db.Column(db.Integer, primary_key=True)
    method_db_id = db.Column(db.String(255), default='')
    otu_id = db.Column(db.Integer, db.ForeignKey('otus.id', ondelete='CASCADE'), index=True)
    method_id = db.Column(db.Integer, db.ForeignKey('otu_classification_methods.id', ondelete='CASCADE'), index=True)

    def __init__(self, method_db_id, otu_id, method_id):
        self.method_db_id = method_db_id
        self.otu_id = otu_id
        self.method_id = method_id
    
    def __repr__(self):
        return str(self.id) + ". " + self.otu_id + " " + self.method_db_id
    
    @staticmethod
    def add_otu_classification_from_table(otu_classification_table,
                                    otu_classification_description,
                                    classifier_name,
                                    classifier_version,
                                    classification_ref_db,
                                    classification_ref_db_release):
        """
        Function to add OTU classification to the database

        :param otu_classification_table: path to the file with OTU classification
        :param otu_classification_description: description of the OTU classification method
        :param classifier_name: classifier used to classify the OTUs
        :param classifier_version: version of the classifier used
        :param classification_ref_db: reference database used in classification
        :param classification_ref_db_release: release of the reference database used
        """
        
        new_classification_method = OTUClassificationMethod(otu_classification_description,
                                    classifier_name, classifier_version,
                                    classification_ref_db, classification_ref_db_release)
        
        db.session.add(new_classification_method)
        db.session.commit()

        classified_otus = 0
        new_otu_classifications = []

        with open(otu_classification_table, 'r') as fin:

            _ = fin.readline()

            for line in fin:
                parts = line.strip().split('\t')

                if len(parts) == 2:

                    otu_name, path = parts

                    otu_record = OperationalTaxonomicUnit.query.filter_by(original_id=otu_name).first()

                    if classification_ref_db == 'silva':
                        taxon_db_record = SILVATaxon.query.filter_by(taxon_path=path).first()
                        print('Using SILVA !!!!!!!\n\n\n\n\n\n')
                    elif classification_ref_db == 'greengenes':
                        taxon_db_record = GGTaxon.query.filter_by(taxon_path=path).first()
                        print('Using GreenGenes !!!!!!!\n\n\n\n\n\n')

                    print('reference_database:', classification_ref_db, '\n\n\n\n\n\n\n\n\n')
                    print('path:', path, '\n\n\n\n\n\n\n\n\n')

                    new_otu_classification = OTUClassification(taxon_db_record.id,\
                                                               otu_record.id,\
                                                               new_classification_method.id)

                    db.session.add(new_otu_classification)
                    classified_otus+=1
                    new_otu_classifications.append(new_otu_classification)

                    if len(new_otu_classifications) > 400:
                        db.session.commit()
                        new_otu_classifications = []

            db.session.commit()
        
        return classified_otus
    
    @staticmethod
    def get_ncbi_from_gg_taxonomy(gg_taxonomy_path):
        """
        Get NCBI taxid from GreenGenes taxonomy path

        :param gg_taxonomy_path: GG taxonomy path (e.g., gg_13_5_taxonomy.txt)
        :return: 
        """

        new_taxons = []
        taxon_count = 0

        

        # add the last set of sequences
        db.session.commit()

        return taxon_count