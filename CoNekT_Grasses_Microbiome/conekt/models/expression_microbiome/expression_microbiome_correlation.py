from conekt import db

import json

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

from conekt.models.studies import Study
from conekt.models.relationships.study_sample import StudySampleAssociation
from conekt.models.expression.profiles import ExpressionProfile
from conekt.models.microbiome.otu_profiles import OTUProfile
from conekt.models.sequences import Sequence

from corals.threads import set_threads_for_external_libraries
set_threads_for_external_libraries(n_threads=1)
import numpy as np
from corals.correlation.full.default import cor_full
from corals.correlation.utils import derive_pvalues, multiple_test_correction

import pandas as pd

class ExpMicroCorrelationMethod(db.Model):
    __tablename__ = 'expression_microbiome_correlation_methods'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    sample_group = db.Column(db.String(255, collation=SQL_COLLATION), default='whole study')
    tool_name = db.Column(db.Enum('SparXCC', 'corALS', name='Tool'), default='corALS')
    stat_method = db.Column(db.Enum('sparxcc', 'pearson', 'spearman', name='Statistical Method'), default='pearson')
    multiple_test_cor_method = db.Column(db.Enum('fdr_bh', 'bonferroni', name='P-value correction Method'), default=None)
    rnaseq_norm = db.Column(db.Enum('numreads', 'cpm', 'tpm', 'tmm', name='RNA-seq Normalization'), default='tpm')
    metatax_norm = db.Column(db.Enum('numreads', 'cpm', 'tpm', 'tmm', name='Metataxonomic Normalization'), default='numreads')
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'), index=True)

    exp_microbiome_correlations = db.relationship('ExpMicroCorrelation',
                                    backref=db.backref('method', lazy='joined'),
                                    lazy='dynamic',
                                    cascade="all, delete-orphan",
                                    passive_deletes=True)

    def __init__(self, description, sample_group, tool_name, stat_method,
                 multiple_test_cor_method, rnaseq_norm,
                 metatax_norm, study_id):
        self.description = description
        self.sample_group = sample_group
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
    otu_probe = db.Column(db.String(255, collation=SQL_COLLATION), index=True)
    gene_probe = db.Column(db.String(255, collation=SQL_COLLATION), index=True)
    exp_micro_correlation_method_id = db.Column(db.Integer, db.ForeignKey('expression_microbiome_correlation_methods.id', ondelete='CASCADE'), index=True)

    def __init__(self, expression_profile_id, metatax_profile_id,
                 exp_micro_correlation_method_id,
                 corr_coef, pvalue, qvalue, otu_probe, gene_probe):
        self.expression_profile_id = expression_profile_id
        self.metatax_profile_id = metatax_profile_id
        self.exp_micro_correlation_method_id = exp_micro_correlation_method_id
        self.corr_coef = corr_coef
        self.pvalue = pvalue
        self.qvalue = qvalue
        self.otu_probe = otu_probe
        self.gene_probe = gene_probe
    
    def __repr__(self):
        return str(self.id)

    @staticmethod
    def calculate_expression_metataxonomic_correlations(study_id, description, tool, stat_method, multiple_test_cor_method,
                                                        rnaseq_norm, metatax_norm, correlation_cutoff=0.5,
                                                        corrected_pvalue_cutoff=0.05):
        """
        Function to calculate the correlations between expression and metataxonomic profiles

        :param study_id: internal id of the study
        :param tool: tool used to calculate the correlation
        :param stat_method: Pearson or Spearman correlation
        :param multiple_test_cor_method: Bonferroni (currently, FDR is not implemented due to requirements of large memory with the full correlation)
        :param rnaseq_norm: normalization method used for the RNA-seq data
        :param metatax_norm: normalization method used for the metataxonomic data
        :param correlation_cutoff: cutoff value for the correlation
        :param corrected_pvalue_cutoff: cutoff value for the corrected p-value
        """

        new_correlation_method = ExpMicroCorrelationMethod(description, tool, stat_method, multiple_test_cor_method,
                                                            rnaseq_norm, metatax_norm, study_id)
        
        db.session.add(new_correlation_method)
        db.session.commit()

        # Get study
        study = Study.query.get(study_id)

        # Get all sample ids associated with study
        study_samples = StudySampleAssociation.query.filter_by(study_id=study.id).all()
        study_sample_ids = [sample.sample_id for sample in study_samples]

        # Get all expression profiles associated with study
        expression_profiles = ExpressionProfile.query.filter_by(normalization_method=rnaseq_norm,
                                                                species_id=study.species_id).all()
        # Get all OTU profiles associated with study
        metatax_profiles = OTUProfile.query.filter_by(normalization_method=metatax_norm,
                                                         species_id=study.species_id).all()
        
        # Create pandas dataframe with all expression and metatax profiles associated with study
        expression_profiles_df = pd.DataFrame()
        exp_run2sample_id = {}

        # Add rows to the dataframe from JSON
        for profile in expression_profiles:
            profile_dict = json.loads(profile.profile)
            study_runs = [r for r in profile_dict['data']['sample_id'].keys() if profile_dict['data']['sample_id'][r] in study_sample_ids]
            if expression_profiles_df.empty:
                expression_profiles_df = pd.DataFrame(columns = study_runs)
                exp_run2sample_id = profile_dict['data']['sample_id']
            df_the_dict = pd.DataFrame(dict(map(lambda key: (key, profile_dict['data']['exp_value'].get(key, None)), study_runs)), index=[str(profile.probe)])
            expression_profiles_df = pd.concat([expression_profiles_df, df_the_dict])

        expression_profiles_df = expression_profiles_df.rename(columns=exp_run2sample_id)
        
        metatax_profiles_df = pd.DataFrame()
        metatax_run2sample_id = {}

        for profile in metatax_profiles:
            profile_dict = json.loads(profile.profile)
            study_runs = [r for r in profile_dict['data']['sample_id'].keys() if profile_dict['data']['sample_id'][r] in study_sample_ids]
            if metatax_profiles_df.empty:
                metatax_profiles_df = pd.DataFrame(columns = study_runs)
                metatax_run2sample_id = profile_dict['data']['sample_id']
            df_the_dict = pd.DataFrame(dict(map(lambda key: (key, profile_dict['data']['count'].get(key, None)), study_runs)), index=[str(profile.probe)])
            metatax_profiles_df = pd.concat([metatax_profiles_df, df_the_dict])
        
        metatax_profiles_df = metatax_profiles_df.rename(columns=metatax_run2sample_id)
        concat_df = pd.concat([expression_profiles_df, metatax_profiles_df], axis=0)
        concatenated_transposed = concat_df.transpose()
        cor_values = cor_full(concatenated_transposed, correlation_type=stat_method)

        # Getting number of samples and features (genes/OTUs)
        n_samples = concatenated_transposed.shape[0]
        n_features = concatenated_transposed.shape[1]

        # Get the p-values and correct them
        pvalues = derive_pvalues(cor_values, n_samples)
        pvalues_corrected = multiple_test_correction(pvalues, n_features, method=multiple_test_cor_method)

        true_positions_cor = np.where(cor_values > correlation_cutoff)
        true_positions_pvalue = np.where(pvalues_corrected < corrected_pvalue_cutoff)

        # Filtering correlations based on coef. and corrected pvalues
        cor_tuples = []
        pval_tuples = []

        for i in range(np.size(true_positions_cor, 1)):
            cor_tuples.append((true_positions_cor[0][i],
            true_positions_cor[1][i]))

        for i in range(np.size(true_positions_pvalue, 1)):
            pval_tuples.append((true_positions_pvalue[0][i],
            true_positions_pvalue[1][i]))

        cor_tuples_set = set(cor_tuples)
        pval_tuples_set = set(pval_tuples)

        cor_pval_intersection = cor_tuples_set.intersection(pval_tuples_set)
        cor_pval_intersection_tuple = ([t[0] for t in list(cor_pval_intersection)],
        [t[1] for t in list(cor_pval_intersection)])

        shape_row = expression_profiles_df.shape[0]

        for i in range(len(cor_pval_intersection_tuple[0])):
            if (cor_pval_intersection_tuple[1][i] > (shape_row - 1)) and (cor_pval_intersection_tuple[0][i] < shape_row):
                otu_p = OTUProfile.query.filter_by(probe=str(cor_values.columns[cor_pval_intersection_tuple[1][i]]),
                                                         species_id=study.species_id).first()
                exp_p = ExpressionProfile.query.filter_by(probe=str(cor_values.index[cor_pval_intersection_tuple[0][i]]),
                                                species_id=study.species_id).first()
                new_correlation_pair = ExpMicroCorrelation(exp_p.id, otu_p.id, new_correlation_method.id,
                                                           cor_values.iloc[cor_pval_intersection_tuple[0][i], cor_pval_intersection_tuple[1][i]],
                                                           pvalues_corrected[cor_pval_intersection_tuple[0][i], cor_pval_intersection_tuple[1][i]])
                db.session.add(new_correlation_pair)

                if i % 400 == 0:
                    db.session.commit()

        db.session.commit()

        # Return the calculated correlations
        return True

    @staticmethod
    def add_expression_metataxonomic_correlations(study_id, description, sample_group,
                                                  stat_method, matrix_file):
        """
        Add correlations between expression and metataxonomic profiles
        Currently, only SparXCC is implemented
        
        :param study_id: internal id of the study
        :param description: description of the correlation
        :param sample_group: sample group to calculate the correlation
        :param stat_method: Pearson, Spearman or SparXCC correlation
        :param matrix_file: path to the matrix file
        """

        if stat_method == 'sparxcc':

            # In case of SparXCC, tool name and statistical method are the same
            # Also, counts are always used, not normalized values,
            # so 'numreads' is used for both metatax_norm and rnaseq_norm
            new_correlation_method = ExpMicroCorrelationMethod(description=description, tool_name='SparXCC', stat_method='sparxcc',
                                                                study_id=study_id, sample_group=sample_group,
                                                                rnaseq_norm='numreads', metatax_norm='numreads',
                                                                multiple_test_cor_method=None)
    
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


    @staticmethod
    def create_custom_network(cor_method_id, probes):
        """
        Return a network dict for a certain set of probes/sequences, for a certain study and method

        :param method_id: network method to extract information from
        :param probes: list of probe/sequence names
        :return: network dict
        """
        nodes = []
        edges = []

        sequences = Sequence.query.filter(Sequence.name.in_(probes)).filter_by(type='protein_coding').all()

        valid_nodes = []

        for s in sequences:
            gene_node = {"id": str(s.id) + "_gene",
                    "name": s.name,
                    "node_type": "gene",
                    "depth": 0}

            valid_nodes.append(s.name)
            nodes.append(gene_node)

        existing_edges = []

        for s in sequences:
            source = str(s.id) + "_gene"
            expression_microbiome_correlations = ExpMicroCorrelation.query.filter_by(exp_micro_correlation_method_id=cor_method_id).all()
            for cor_result in expression_microbiome_correlations:
                otu_profile = OTUProfile.query.filter_by(id=cor_result.metatax_profile_id).first()
                if otu_profile.probe in valid_nodes:
                    continue
                otu_node = {"id": str(otu_profile.otu_id) + "_otu",
                    "name": str(otu_profile.probe),
                    "node_type": "otu",
                    "depth": 0}
                nodes.append(otu_node)
                valid_nodes.append(str(otu_profile.probe))
                edges.append({"source": source,
                                "target": str(otu_profile.otu_id) + "_otu",
                                "source_name": s.name,
                                "target_name": otu_profile.probe,
                                "depth": 0,
                                "link_pcc": cor_result.corr_coef,
                                "edge_type": "correlation",
                                "correlation_method": cor_result.method.stat_method})
                existing_edges.append([source, cor_result.metatax_profile_id])
                existing_edges.append([cor_result.metatax_profile_id, source])

        return {"nodes": nodes, "edges": edges}

