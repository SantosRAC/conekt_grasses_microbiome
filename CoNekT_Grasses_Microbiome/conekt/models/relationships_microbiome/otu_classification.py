from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class OTUClassificationMethod(db.Model):
    __tablename__ = 'otu_classification_methods'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    classifier_name = db.Column(db.Enum('uclust', 'other', name=''),
                                default='uclust')
    classifier_version = db.Column(db.String(255), default='')
    ref_database = db.Column(db.Enum('greengenes', 'silva', 'other', name=''),
                             default='silva')
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


class OTUClassification(db.Model):
    __tablename__ = 'otu_classification'
    id = db.Column(db.Integer, primary_key=True)
    otu_id = db.Column(db.Integer, db.ForeignKey('otus.id', ondelete='CASCADE'), index=True)
    ncbi_id = db.Column(db.Integer, db.ForeignKey('ncbi_taxonomy.id', ondelete='CASCADE'), index=True)
    silva_id = db.Column(db.Integer, db.ForeignKey('silva_taxonomy.id', ondelete='CASCADE'), index=True)
    method_id = db.Column(db.Integer, db.ForeignKey('otu_classification_methods.id', ondelete='CASCADE'), index=True)

    def __init__(self, otu_id, ncbi_id, silva_id, method_id):
        self.otu_id = otu_id
        self.ncbi_id = ncbi_id
        self.silva_id = silva_id
        self.method_id = method_id
    
    def __repr__(self):
        return str(self.id) + ". " + self.asv_id + " " + self.silva_id