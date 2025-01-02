from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

from conekt.models.studies import Study


class MicroAssociationMethod(db.Model):
    __tablename__ = 'otu_association_methods'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    sample_group = db.Column(db.String(255, collation=SQL_COLLATION), default='whole study')
    tool_name = db.Column(db.Enum('SparCC', 'Spieac-Easi', name='Tool'), default='Spiec-Easi')
    method = db.Column(db.Enum('spiec-easi-mb', 'spiec-easi-glasso', name='Method'), default=None)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'), index=True)

    def __init__(self, description, sample_group, tool_name, method, study_id):
        self.description = description
        self.sample_group = sample_group
        self.tool_name = tool_name
        self.method = method
        self.study_id = study_id
    
    def __repr__(self):
        return str(self.id)


class MicroAssociation(db.Model):
    __tablename__ = 'otu_associations'
    id = db.Column(db.Integer, primary_key=True)
    association_value = db.Column(db.Float)
    metatax_profile_id = db.Column(db.Integer, db.ForeignKey('otu_profiles.id', ondelete='CASCADE'), index=True)
    otu_probe = db.Column(db.String(255, collation=SQL_COLLATION), index=True)
    otu_association_method_id = db.Column(db.Integer, db.ForeignKey('otu_association_methods.id', ondelete='CASCADE'), index=True)

    def __init__(self, metatax_profile_id, otu_association_method_id,
                 association_value, otu_probe):
        self.metatax_profile_id = metatax_profile_id
        self.otu_association_method_id = otu_association_method_id
        self.association_value = association_value
        self.otu_probe = otu_probe
    
    def __repr__(self):
        return str(self.id)
    

    @staticmethod
    def add_otu_associations(study_id, sample_group, description, tool_name, method):
        """
        Add associations between expression and metataxonomic profiles
        Currently, only SparXCC is implemented
        
        :param study_id: internal id of the study
        :param sample_group: sample group to calculate the correlation
        :param method: Pearson, Spearman or SparXCC correlation
        :param matrix_file: path to the matrix file
        """

        if stat_method == 'sparxcc':

            # In case of SparXCC, tool name and statistical method are the same
            # Also, counts are always used, not normalized values,
            # so 'numreads' is used for both metatax_norm and rnaseq_norm
            new_correlation_method = ExpMicroCorrelationMethod(description=description, tool_name='Spieac-Easi', method='spiec-easi-mb',
                                                                study_id=study_id, sample_group=sample_group)

            db.session.add(new_correlation_method)
            db.session.commit()

            # Get study
            study = Study.query.get(study_id)
            
            with open(matrix_file, 'r') as fin:
                
                colnames = fin.readline().rstrip().split()
                halfmatrix = int(len(colnames) / 2)
                gene_names = [n.replace('cor.','').replace('"', '') for n in colnames[:halfmatrix]]

                for line in fin:
                    otu_name, *line_fields = line.rstrip().split()
                    otu_name = otu_name.replace('"', '')

                    # Retrieve the correlation matrix, the m value and the boolean matrix
                    correlations_matrix = line_fields[:halfmatrix]
                    m_boolean_matrix = line_fields[halfmatrix + 1:]

                    # Get significant correlations
                    for i, val in enumerate(m_boolean_matrix):
                        if val == 'TRUE':

                            otu_p = OTUProfile.query.filter_by(probe=otu_name,
                                species_id=study.species_id).first()

                            exp_p = ExpressionProfile.query.filter_by(probe=gene_names[i],
                                species_id=study.species_id).first()

                            new_correlation_pair = ExpMicroCorrelation(otu_probe=otu_name,
                                                                       gene_probe=gene_names[i],
                                                                       expression_profile_id=exp_p.id,
                                                                       metatax_profile_id=otu_p.id,
                                                                       exp_micro_correlation_method_id=new_correlation_method.id,
                                                                       corr_coef=correlations_matrix[i],
                                                                       pvalue=None,
                                                                       qvalue=None)

                            db.session.add(new_correlation_pair)

                            if i % 400 == 0:
                                db.session.commit()

                    db.session.commit()