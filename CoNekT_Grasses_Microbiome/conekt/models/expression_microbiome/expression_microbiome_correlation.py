from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class ExpMicroCorrelation(db.Model):
    __tablename__ = 'expression_microbiome_correlations'
    id = db.Column(db.Integer, primary_key=True)
    stat_method = db.Column(db.Enum('pearson', 'spearman', name='Statistical Method'), default='pearson')
    pvalue = db.deferred(db.Column(db.Float))
    corr_coef = db.deferred(db.Column(db.Float))

    expression_profile_id = db.Column(db.Integer, db.ForeignKey('expression_profiles.id', ondelete='CASCADE'), index=True)
    asv_profile_id = db.Column(db.Integer, db.ForeignKey('asv_profiles.id', ondelete='CASCADE'), index=True)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'), index=True)

    def __init__(self, stat_method, pvalue, corr_coef,
                 expression_profile_id, asv_profile_id, study_id):
        self.stat_method = stat_method
        self.pvalue = pvalue
        self.corr_coef = corr_coef
        self.expression_profile_id = expression_profile_id
        self.asv_profile_id = asv_profile_id
        self.study_id = study_id
    
    def __repr__(self):
        return str(self.id)
    
    @staticmethod
    def calculate_expression_asvs_correlations(study_id):

        #TODO: implement this method 


