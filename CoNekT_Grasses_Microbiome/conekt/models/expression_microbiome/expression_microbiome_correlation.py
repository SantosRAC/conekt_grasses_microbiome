from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

from conekt.models.studies import Study
from conekt.models.expression.profiles import ExpressionProfile


class ExpMicroCorrelationMethod(db.Model):
    __tablename__ = 'expression_microbiome_correlation_methods'
    id = db.Column(db.Integer, primary_key=True)
    tool_name = db.Column(db.Enum('corALS', name='Tool'), default='corALS')
    stat_method = db.Column(db.Enum('pearson', 'spearman', name='Statistical Method'), default='pearson')
    multiple_test_cor_method = db.Column(db.Enum('fdr_bh', 'bonferroni', name='P-value correction Method'), default='fdr_bh')
    rnaseq_norm = db.Column(db.Enum('numreads', 'cpm', 'tpm', 'tmm', name='RNA-seq Normalization'), default='tpm')
    metatax_norm = db.Column(db.Enum('numreads', 'cpm', 'tpm', 'tmm', name='Metataxonomic Normalization'), default='numreads')
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'), index=True)

    def __init__(self, tool_name, stat_method, multiple_test_cor_method,
                 rnaseq_norm, metatax_norm, study_id):
        self.tool_name = tool_name
        self.stat_method = stat_method
        self.multiple_test_cor_method = multiple_test_cor_method
        self.rnaseq_norm = rnaseq_norm
        self.metatax_norm = metatax_norm
        self.study_id = study_id
    
    def __repr__(self):
        return str(self.id)


class ExpMicroCorrelation(db.Model):
    __tablename__ = 'expression_microbiome_correlations'
    id = db.Column(db.Integer, primary_key=True)
    pvalue = db.Column(db.Float)
    qvalue = db.Column(db.Float)
    corr_coef = db.Column(db.Float)

    expression_profile_id = db.Column(db.Integer, db.ForeignKey('expression_profiles.id', ondelete='CASCADE'), index=True)
    metatax_profile_id = db.Column(db.Integer, db.ForeignKey('otu_profiles.id', ondelete='CASCADE'), index=True)
    exp_micro_correlation_method_id = db.Column(db.Integer, db.ForeignKey('expression_microbiome_correlation_methods.id', ondelete='CASCADE'), index=True)

    def __init__(self, pvalue, qvalue, corr_coef, expression_profile_id,
                 metatax_profile_id, exp_micro_correlation_method_id):
        self.pvalue = pvalue
        self.qvalue = qvalue
        self.corr_coef = corr_coef
        self.expression_profile_id = expression_profile_id
        self.metatax_profile_id = metatax_profile_id
        self.exp_micro_correlation_method_id = exp_micro_correlation_method_id
    
    def __repr__(self):
        return str(self.id)

    @staticmethod
    def calculate_expression_metataxonomic_correlations(study_id, tool, stat_method, multiple_test_cor_method,
                                                        rnaseq_norm, metatax_norm):
        """
        Function to calculate the correlations between expression and metataxonomic profiles

        :param study_id: internal id of the study
        :param tool: tool used to calculate the correlation
        :param stat_method: Pearson or Spearman correlation
        :param multiple_test_cor_method: FDR or Bonferroni
        :param rnaseq_norm: normalization method used for the RNA-seq data
        :param metatax_norm: normalization method used for the metataxonomic data
        """

        new_correlation_method = ExpMicroCorrelationMethod(tool, stat_method, multiple_test_cor_method,
                                                            rnaseq_norm, metatax_norm, study_id)
        
        db.session.add(new_correlation_method)
        db.session.commit()

        # Get study
        study = Study.query.get(study_id)

        # Get all expression profiles

        

        

        

        

        

        


        


