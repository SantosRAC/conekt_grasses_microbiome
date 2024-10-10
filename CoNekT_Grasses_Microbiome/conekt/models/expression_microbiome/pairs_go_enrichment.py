from conekt import db

from conekt.models.studies import Study
from conekt.models.expression_microbiome.expression_microbiome_correlation import ExpMicroCorrelationMethod

class GroupCorPairsGOEnrichment(db.Model):
    __tablename__ = 'group_correlated_pairs_go_enrichment'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    cor_method_id = db.Column(db.Integer, db.ForeignKey('expression_microbiome_correlation_methods.id', ondelete='CASCADE'))
    go_id = db.Column(db.Integer, db.ForeignKey('go.id', ondelete='CASCADE'))
    threshold_correlation_value = db.Column(db.Float)
    enrichment = db.Column(db.Float)
    p_value = db.Column(db.Float)
    corrected_p_value = db.Column(db.Float)

    def __init__(self, cor_method_id, go_id, threshold_correlation_value,
                 enrichment, p_value, corrected_p_value):
        self.cor_method_id = cor_method_id
        self.go_id = go_id
        self.threshold_correlation_value = threshold_correlation_value
        self.enrichment = enrichment
        self.p_value = p_value
        self.corrected_p_value = corrected_p_value        
    
    def __repr__(self):
        return str(self.id)

    @staticmethod
    def add_go_enrichment_expression_metataxonomic_correlations(study_id, exp_micro_correlation_method_id,
                                                                go_enrichment_file, go_enrichment_method='goatools'):
        """
        Add GO enrichment for correlations between expression and metataxonomic profiles
        
        :param study_id: internal id of the study
        :param go_enrichment_method: method used for GO enrichment
        :param exp_micro_correlation_method_id: internal id of the correlation method
        :param go_enrichment_file: file with the GO enrichment data        
        """
        
        # Get study
        study = Study.query.get(study_id)
        correlation_method = ExpMicroCorrelationMethod.query.get(exp_micro_correlation_method_id)
        
        with open(go_enrichment_file, 'r') as fin:
            
            _ = fin.readline()

            for line in fin:


                new_correlation_pair = GroupCorPairsGOEnrichment()
                db.session.add(new_correlation_pair)

                if i % 400 == 0:
                    db.session.commit()

            db.session.commit()