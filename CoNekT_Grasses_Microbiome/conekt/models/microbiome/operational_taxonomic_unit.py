from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class OperationalTaxonomicUnitMethod(db.Model):
    __tablename__ = 'otu_methods'
    id = db.Column(db.Integer, primary_key=True)
    clustering_method = db.Column(db.Enum('de_novo', 'closed_reference', 'open_reference', name='Clustering Method'), default='de_novo')
    clustering_threshold = db.Column(db.Float)
    clustering_algorithm = db.Column(db.Enum('vsearch', 'usearch', 'swarm', 'dada2', 'deblur', 'qiime1', name='Clustering Algorithm'), default='vsearch')
    clustering_reference_database = db.Column(db.String(255), default='')
    clustering_reference_db_release = db.Column(db.String(255), default='')
    amplicon_marker = db.Column(db.Enum('16S', 'ITS', name='sequence_type'), default='16S')
    primer_pair = db.Column(db.String(255), default='')
    literature_id = db.Column(db.Integer, db.ForeignKey('literature.id', ondelete='CASCADE'), index=True)

    def __init__(self, clustering_method, clustering_threshold,
                 clustering_algorithm, clustering_reference_database,
                 clustering_reference_db_release):
        self.clustering_method = clustering_method
        self.clustering_threshold = clustering_threshold
        self.clustering_algorithm = clustering_algorithm
        self.clustering_reference_database = clustering_reference_database
        self.clustering_reference_db_release = clustering_reference_db_release
    
    def __repr__(self):
        return str(self.id) + ". " + self.method_id (self.clustering_method, self.clustering_algorithm)

class OperationalTaxonomicUnit(db.Model):
    __tablename__ = 'otus'
    id = db.Column(db.Integer, primary_key=True)
    representative_sequence = db.deferred(db.Column(LONGTEXT))
    method_id = db.Column(db.Integer, db.ForeignKey('otu_methods.id', ondelete='CASCADE'), index=True)

    otus_profiles = db.relationship('OTUProfile', backref=db.backref('asv', lazy='joined'),
                                          lazy='dynamic',
                                          cascade="all, delete-orphan",
                                          passive_deletes=True)

    def __init__(self, representative_sequence, method_id):
        self.representative_sequence = representative_sequence
        self.method_id = method_id
    
    def __repr__(self):
        return str(self.id) + ". " + self.method_id

    @staticmethod
    def add_otus_from_fasta():
        
        #TODO: implement function