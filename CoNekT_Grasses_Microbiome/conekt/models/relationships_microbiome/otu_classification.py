from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

from conekt.models.taxonomy import GGTaxon, SILVATaxon, GTDBTaxon
from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit

class OTUClassificationMethod(db.Model):
    __tablename__ = 'otu_classification_methods'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    classifier_name = db.Column(db.Enum('uclust', 'qiime2_classify-sklearn', 'other', name=''),
                                default='uclust')
    classifier_version = db.Column(db.String(255), default='')
    classification_ref_db = db.Column(db.Enum('greengenes', 'silva', 'gtdb', 'other', name=''),
                             default='gtdb')
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


class OTUClassificationGG(db.Model):
    __tablename__ = 'otu_classification_gg'
    id = db.Column(db.Integer, primary_key=True)
    gg_id = db.Column(db.Integer, db.ForeignKey('gg_taxonomy.id'), index=True)
    otu_id = db.Column(db.Integer, db.ForeignKey('otus.id', ondelete='CASCADE'), index=True)
    method_id = db.Column(db.Integer, db.ForeignKey('otu_classification_methods.id', ondelete='CASCADE'), index=True)

    def __init__(self, gg_id, otu_id, method_id):
        self.gg_id = gg_id
        self.otu_id = otu_id
        self.method_id = method_id
    
    def __repr__(self):
        return str(self.id) + ". " + self.otu_id + " " + self.method_id
    
    @staticmethod
    def add_otu_classification_from_table(otu_classification_table,
                                    otu_classification_description,
                                    classifier_name,
                                    classifier_version,
                                    classification_ref_db_release):
        """
        Function to add OTU classification from GG to the database

        :param otu_classification_table: path to the file with OTU classification
        :param otu_classification_description: description of the OTU classification method
        :param classifier_name: classifier used to classify the OTUs
        :param classifier_version: version of the classifier used
        :param classification_ref_db_release: release of the reference database used
        """
        
        new_classification_method = OTUClassificationMethod(otu_classification_description,
                                    classifier_name, classifier_version, 'greengenes',
                                    classification_ref_db_release)
        
        db.session.add(new_classification_method)
        db.session.commit()

        classified_otus = 0
        new_otu_classifications = []

        with open(otu_classification_table, 'r') as fin:

            _ = fin.readline()
            #OTU	path

            for line in fin:
                parts = line.strip().split('\t')

                if len(parts) == 2:

                    otu_name, path = parts

                    otu_record = OperationalTaxonomicUnit.query.filter_by(original_id=otu_name).first()

                    # get the GG taxon record
                    #taxon_db_record = GGTaxon.query.filter_by(taxon_path=path).first()

                    # create a new OTU classification record
                    new_otu_classification = OTUClassificationGG(1,
                                                                 #taxon_db_record.id,
                                                                 otu_record.id,
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
    def get_otu_taxonomy(otu_id):
        """
        Function to get the taxonomy of all OTUs
        """

        otu_gg_taxa = OTUClassificationGG.query.filter_by(otu_id=otu_id).all()

        otu_taxonomy = []

        if otu_gg_taxa:
            for otu_gg_taxon in otu_gg_taxa:
                gg_taxon = GGTaxon.query.filter_by(id=otu_gg_taxon.gg_id).first()
                otu_taxonomy.append([gg_taxon.id, gg_taxon.taxon_path])

        return otu_taxonomy


# class OTUClassificationGTDB(db.Model):
#     __tablename__ = 'otu_classification_gtdb'
#     id = db.Column(db.Integer, primary_key=True)
#     gtdb_id = db.Column(db.Integer, db.ForeignKey('gtdb_taxonomy.id'), index=True)
#     otu_id = db.Column(db.Integer, db.ForeignKey('otus.id', ondelete='CASCADE'), index=True)
#     method_id = db.Column(db.Integer, db.ForeignKey('otu_classification_methods.id', ondelete='CASCADE'), index=True)

#     def __init__(self, gtdb_id, otu_id, method_id):
#         self.gtdb_id = gtdb_id
#         self.otu_id = otu_id
#         self.method_id = method_id
    
#     def __repr__(self):
#         return str(self.id) + ". " + self.otu_id + " " + self.method_id
    
#     @staticmethod
#     def add_otu_classification_from_table(otu_classification_table,
#                                     otu_classification_description,
#                                     classifier_name,
#                                     classifier_version,
#                                     classification_ref_db_release):
        """
        Function to add OTU classification from GTDB to the database

        :param otu_classification_table: path to the file with OTU classification
        :param otu_classification_description: description of the OTU classification method
        :param classifier_name: classifier used to classify the OTUs
        :param classifier_version: version of the classifier used
        :param classification_ref_db_release: release of the reference database used
        """
        
        new_classification_method = OTUClassificationMethod(otu_classification_description,
                                    classifier_name, classifier_version, 'gtdb',
                                    classification_ref_db_release)
        
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

                    taxon_db_record = GTDBTaxon.query.filter_by(taxon_path=path).first()

                    new_otu_classification = OTUClassificationGTDB(taxon_db_record.id,
                                                                 otu_record.id,
                                                                 new_classification_method.id)

                    db.session.add(new_otu_classification)
                    classified_otus+=1
                    new_otu_classifications.append(new_otu_classification)

                    if len(new_otu_classifications) > 400:
                        db.session.commit()
                        new_otu_classifications = []

            db.session.commit()
        
        return classified_otus