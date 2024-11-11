from conekt import db

import json

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

from conekt.models.studies import Study
from conekt.models.relationships.study_sample import StudySampleAssociation
from conekt.models.expression.profiles import ExpressionProfile
from conekt.models.microbiome.otu_profiles import OTUProfile
from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit
from conekt.models.sequences import Sequence


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
    def create_custom_network(cor_method_id, gene_probes, otu_probes):
        """
        Return a network dict for a certain set of probes/sequences, for a certain study and method

        :param method_id: network method to extract information from
        :param gene_probes: list of probe/gene sequence names
        :param otu_probes: list of probe/otu sequence names
        :return: network dict
        """
        gene_nodes = []
        otu_nodes = []
        edges = []

        gene_sequences = Sequence.query.filter(Sequence.name.in_(gene_probes)).filter_by(type='protein_coding').all()
        otu_sequences = OperationalTaxonomicUnit.query.filter(OperationalTaxonomicUnit.original_id.in_(otu_probes)).all()

        valid_gene_nodes = []
        valid_otu_nodes = []

        for s in gene_sequences:
            gene_node = {"id": str(s.id) + "_gene",
                    "name": s.name,
                    "node_type": "gene",
                    "depth": 0}

            valid_gene_nodes.append(s.name)
            gene_nodes.append(gene_node)

        for s in otu_sequences:
            otu_node = {"id": str(s.id) + "_otu",
                    "name": s.original_id,
                    "node_type": "otu",
                    "depth": 0}

            valid_otu_nodes.append(s.original_id)
            otu_nodes.append(otu_node)

        for s in gene_sequences:
            source = str(s.id) + "_gene"
            expression_microbiome_correlations = ExpMicroCorrelation.query.filter_by(exp_micro_correlation_method_id=cor_method_id,
                                                                                     gene_probe=s.name).all()
            for cor_result in expression_microbiome_correlations:
                otu_profile = OTUProfile.query.filter_by(id=cor_result.metatax_profile_id).first()
                if otu_profile.probe not in valid_otu_nodes:
                    otu_node = {"id": str(otu_profile.otu_id) + "_otu",
                    "name": str(otu_profile.probe),
                    "node_type": "otu",
                    "depth": 0}
                    otu_nodes.append(otu_node)
                    valid_otu_nodes.append(str(otu_profile.probe))
                edges.append({"source": source,
                                "target": str(otu_profile.otu_id) + "_otu",
                                "source_name": s.name,
                                "target_name": otu_profile.probe,
                                "depth": 0,
                                "link_cc": cor_result.corr_coef,
                                "edge_type": "correlation",
                                "correlation_method": cor_result.method.stat_method})
        
        for s in otu_sequences:
            source = str(s.id) + "_otu"
            expression_microbiome_correlations = ExpMicroCorrelation.query.filter_by(exp_micro_correlation_method_id=cor_method_id,
                                                                                     otu_probe=s.original_id).all()
            for cor_result in expression_microbiome_correlations:
                gene_profile = ExpressionProfile.query.filter_by(id=cor_result.expression_profile_id).first()
                if gene_profile.probe not in valid_gene_nodes:
                    gene_node = {"id": str(gene_profile.sequence_id) + "_gene",
                    "name": str(gene_profile.probe),
                    "node_type": "gene",
                    "depth": 0}
                    gene_nodes.append(gene_node)
                    valid_gene_nodes.append(str(gene_profile.probe))
                has_edge = [ed for ed in edges if (ed["source"]==source and ed["target"]==str(gene_profile.sequence_id) + "_gene") or\
                    (ed["source"]==str(gene_profile.sequence_id) + "_gene" and ed["target"]==source)]
                if not has_edge:
                    edges.append({"source": source,
                                "target": str(gene_profile.sequence_id) + "_gene",
                                "source_name": s.original_id,
                                "target_name": gene_profile.probe,
                                "depth": 0,
                                "link_cc": cor_result.corr_coef,
                                "edge_type": "correlation",
                                "correlation_method": cor_result.method.stat_method})

        return {"nodes": otu_nodes+gene_nodes, "edges": edges}

