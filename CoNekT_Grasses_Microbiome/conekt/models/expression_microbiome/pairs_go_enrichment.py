from conekt import db

from conekt.models.go import GO
from conekt.models.expression_microbiome.expression_microbiome_correlation import ExpMicroCorrelationMethod

class GroupCorPairsGOEnrichment(db.Model):
    __tablename__ = 'group_correlated_pairs_go_enrichment'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    cor_method_id = db.Column(db.Integer, db.ForeignKey('expression_microbiome_correlation_methods.id', ondelete='CASCADE'))
    go_id = db.Column(db.Integer, db.ForeignKey('go.id', ondelete='CASCADE'))
    threshold_correlation_value = db.Column(db.Float)
    go_enrichment_method = db.Column(db.String(50))
    enrichment = db.Column(db.Enum('p', 'e', name='enrichment_type'))
    p_value = db.Column(db.Float)
    corrected_p_value = db.Column(db.Float)

    def __init__(self, cor_method_id, go_id, threshold_correlation_value,
                 go_enrichment_method, enrichment, p_value, corrected_p_value):
        self.cor_method_id = cor_method_id
        self.go_id = go_id
        self.threshold_correlation_value = threshold_correlation_value
        self.go_enrichment_method = go_enrichment_method
        self.enrichment = enrichment
        self.p_value = p_value
        self.corrected_p_value = corrected_p_value        
    
    def __repr__(self):
        return str(self.id)

    @staticmethod
    def add_go_enrichment_expression_metataxonomic_correlations(exp_micro_correlation_method_id,
                                                                go_enrichment_file, threshold_correlation_value, go_enrichment_method='goatools'):
        """
        Add GO enrichment for correlations between expression and metataxonomic profiles
        
        :param go_enrichment_method: method used for GO enrichment
        :param exp_micro_correlation_method_id: internal id of the correlation method
        :param threshold_correlation_value: threshold for correlation value
        :param go_enrichment_file: file with the GO enrichment data        
        """
        
        correlation_method = ExpMicroCorrelationMethod.query.get(exp_micro_correlation_method_id)
        
        with open(go_enrichment_file, 'r') as fin:
            
            _ = fin.readline()

            new_go_enrichment_data = []

            for line in fin:

                go_term, _, enrichment_type, _, _, _, p_value, _, _, corrected_p_value_bonferroni, _, _, _, _ = line.strip().split('\t')

                # Remove dots from GO term (GOATOOLS uses gots to indicate GO levels)
                go_term = go_term.replace('.', '')

                selected_go = GO.query.filter_by(label=go_term).first()

                new_go_enrichment = GroupCorPairsGOEnrichment(cor_method_id=correlation_method.id,
                                                              go_id=selected_go.id,
                                                              threshold_correlation_value=threshold_correlation_value,
                                                              go_enrichment_method=go_enrichment_method,
                                                              enrichment=enrichment_type,
                                                              p_value=p_value,
                                                              corrected_p_value=corrected_p_value_bonferroni)

                db.session.add(new_go_enrichment)

                new_go_enrichment_data.append(new_go_enrichment)

                if len(new_go_enrichment_data) > 400:
                    db.session.commit()

            db.session.commit()