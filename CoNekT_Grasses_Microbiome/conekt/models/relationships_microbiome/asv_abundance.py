from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class ASVQuantificationMethod(db.Model):
    __tablename__ = 'asv_quantification_methods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Enum('dada2', 'other', name='data_type'), default='dada2')

    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return str(self.id) + ". " + self.name    


class ASVQuantification(db.Model):
    __tablename__ = 'asv_quantifications'
    id = db.Column(db.Integer, primary_key=True)
    abundance = db.Column(db.Integer, default=0)
    asv_id = db.Column(db.Integer, db.ForeignKey('asvs.id', ondelete='CASCADE'), index=True)
    run_id = db.Column(db.Integer, db.ForeignKey('sequencing_runs.id', ondelete='CASCADE'), index=True)
    method_id = db.Column(db.Integer, db.ForeignKey('asv_abundance_methods.id', ondelete='CASCADE'), index=True)

    def __init__(self, abundance, run_id, method_id):
        self.abundance = abundance
        self.run_id = run_id
        self.method_id = method_id
    
    def __repr__(self):
        return str(self.id) + ". " + self.abundance
    
    @staticmethod
    def add_abundance_from_feature_table(feature_table):
        """
        Function to add ASV abundances to the database

        :param feature_table: path to the file with runs and their ASV abundances
        """


        return 
    


    