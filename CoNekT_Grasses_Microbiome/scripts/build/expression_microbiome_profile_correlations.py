#!/usr/bin/env python3

import argparse

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select

import json
import pandas as pd

# Importing the necessary modules/functions for the correlation calculation
from corals.threads import set_threads_for_external_libraries
set_threads_for_external_libraries(n_threads=1)
import numpy as np
from corals.correlation.full.default import cor_full
from corals.correlation.utils import derive_pvalues, multiple_test_correction


parser = argparse.ArgumentParser(description='Computes correlations between microbiome and expression profiles for a study')
parser.add_argument('--study_id', type=int, metavar='1',
                    dest='study_id',
                    help='Internal id of the study',
                    required=True)
parser.add_argument('--description', type=str, metavar='Correlations between microbiome and expression profiles in this awesome study',
                    dest='cor_method_description',
                    help='Description to the method used to calculate the correlations for one particular study',
                    required=True)
parser.add_argument('--correlation_method', type=str, metavar='pearson',
                    dest='stat_method',
                    help='Method used for the correlation calculation (pearson or spearman)',
                    required=False, default='pearson')
parser.add_argument('--expression_normalization_method', type=str, metavar='tpm',
                    dest='rnaseq_norm',
                    help='Method used to normalize the expression data',
                    required=False, default='tpm')
parser.add_argument('--microbiome_normalization_method', type=str, metavar='cpm',
                    dest='metatax_norm',
                    help='Method used to normalize the microbiome data',
                    required=False, default='cpm')
parser.add_argument('--db_admin', type=str, metavar='DB admin',
                    dest='db_admin',
                    help='The database admin user',
                    required=True)
parser.add_argument('--db_name', type=str, metavar='DB name',
                    dest='db_name',
                    help='The database name',
                    required=True)
parser.add_argument('--db_password', type=str, metavar='DB password',
                    dest='db_password',
                    help='The database password',
                    required=False)

args = parser.parse_args()

if args.db_password:
    db_password = args.db_password
else:
    db_password = input("Enter the database password: ")

def calculate_expression_metataxonomic_correlations(study_id, description, tool, stat_method, multiple_test_cor_method,
                                                        rnaseq_norm, metatax_norm, correlation_cutoff=0.5,
                                                        corrected_pvalue_cutoff=0.05):
        """
        Function to calculate the correlations between expression and metataxonomic profiles

        :param study_id: internal id of the study
        :param tool: tool used to calculate the correlation (currently, only CorALS is implemented)
        :param stat_method: Pearson or Spearman correlation
        :param multiple_test_cor_method: Bonferroni (currently, FDR is not implemented due to requirements of large memory with the full correlation)
        :param rnaseq_norm: normalization method used for the RNA-seq data
        :param metatax_norm: normalization method used for the metataxonomic data
        :param correlation_cutoff: cutoff value for the correlation
        :param corrected_pvalue_cutoff: cutoff value for the corrected p-value
        """

        new_correlation_method = {"description": description,
                                    "tool_name":tool,
                                    "stat_method":stat_method,
                                    "multiple_test_cor_method":multiple_test_cor_method,
                                    "rnaseq_norm":rnaseq_norm, 
                                    "metatax_norm":metatax_norm,
                                    "study_id":study_id}

        new_correlation_method_obj = ExpMicroCorrelationMethod(**new_correlation_method)

        session.add(new_correlation_method_obj)
        session.commit()

        # Get study
        study = session.get(Study, study_id)

        # Get all sample ids associated with study
        with engine.connect() as conn:
            stmt = select(StudySampleAssociation).\
                where(StudySampleAssociation.__table__.c.study_id == study.id)
            study_samples = conn.execute(stmt).all()
            study_sample_ids = [sample.sample_id for sample in study_samples]

        # Get all expression profiles associated with study
        with engine.connect() as conn:
            stmt = select(ExpressionProfile).\
                where(ExpressionProfile.__table__.c.normalization_method == rnaseq_norm,
                      ExpressionProfile.__table__.c.species_id == study.species_id,
                      ExpressionProfile.__table__.c.study_id == study_id)
            expression_profiles = conn.execute(stmt).all()

        # Get all OTU profiles associated with study
        with engine.connect() as conn:
            stmt = select(OTUProfile).\
                where(OTUProfile.__table__.c.normalization_method == metatax_norm,
                      OTUProfile.__table__.c.species_id == study.species_id,
                      OTUProfile.__table__.c.study_id == study_id)
            metatax_profiles = conn.execute(stmt).all()
        
        # Create pandas dataframe with all expression and metatax profiles associated with study
        df_the_dict_expression = {}
        study_runs_expression = []

        # Add rows to the dataframe from JSON
        for profile in expression_profiles:
            profile_dict = json.loads(profile.profile)
            if not study_runs_expression:
                study_runs_expression = [r for r in profile_dict['data']['sample_id'].keys() if profile_dict['data']['sample_id'][r] in study_sample_ids]
            df_the_dict_expression[str(profile.probe)] = dict(map(lambda key: (key, profile_dict['data']['exp_value'].get(key, None)), study_runs_expression))
        
        expression_profiles_df = pd.DataFrame.from_dict(df_the_dict_expression, orient='index')
        expression_profiles_df = expression_profiles_df.rename(columns=profile_dict['data']['sample_id'])

        df_the_dict_metatax = {}
        study_runs_metatax = []

        for profile in metatax_profiles:
            profile_dict = json.loads(profile.profile)
            if not study_runs_metatax:
                study_runs_metatax = [r for r in profile_dict['data']['sample_id'].keys() if profile_dict['data']['sample_id'][r] in study_sample_ids]
            df_the_dict_metatax[str(profile.probe)] = dict(map(lambda key: (key, profile_dict['data']['count'].get(key, None)), study_runs_metatax))
        
        metatax_profiles_df = pd.DataFrame.from_dict(df_the_dict_metatax, orient='index')
        metatax_profiles_df = metatax_profiles_df.rename(columns=profile_dict['data']['sample_id'])

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
                with engine.connect() as conn:
                    stmt = select(OTUProfile).\
                        where(OTUProfile.__table__.c.probe == str(cor_values.columns[cor_pval_intersection_tuple[1][i]]),
                        OTUProfile.__table__.c.species_id == study.species_id,
                        OTUProfile.__table__.c.study_id == study_id)
                    otu_p = conn.execute(stmt).first()
                with engine.connect() as conn:
                    stmt = select(ExpressionProfile).\
                        where(ExpressionProfile.__table__.c.probe == str(cor_values.index[cor_pval_intersection_tuple[0][i]]),
                        ExpressionProfile.__table__.c.species_id == study.species_id,
                        ExpressionProfile.__table__.c.study_id == study_id)
                    exp_p = conn.execute(stmt).first()
                new_correlation_pair = {"expression_profile_id": exp_p.id,
                                        "metatax_profile_id": otu_p.id,
                                        "gene_probe": str(cor_values.index[cor_pval_intersection_tuple[0][i]]),
                                        "otu_probe": str(cor_values.columns[cor_pval_intersection_tuple[1][i]]),
                                        "exp_micro_correlation_method_id": new_correlation_method_obj.id,
                                        "corr_coef": cor_values.iloc[cor_pval_intersection_tuple[0][i], cor_pval_intersection_tuple[1][i]],
                                        "pvalue": pvalues[cor_pval_intersection_tuple[0][i], cor_pval_intersection_tuple[1][i]],
                                        "qvalue": pvalues_corrected[cor_pval_intersection_tuple[0][i], cor_pval_intersection_tuple[1][i]]}
                new_correlation_pair_obj = ExpMicroCorrelation(**new_correlation_pair)
                session.add(new_correlation_pair_obj)

                if i % 400 == 0:
                    session.commit()

        session.commit()

        # Return the calculated correlations
        return True

db_admin = args.db_admin
db_name = args.db_name
study_id = args.study_id
description_method = args.cor_method_description
stat_method = args.stat_method
rnaseq_norm = args.rnaseq_norm
metatax_norm = args.metatax_norm
tool = 'corals'
multiple_test_cor_method = 'bonferroni'
correlation_cutoff=0.5
corrected_pvalue_cutoff=0.05

create_engine_string = "mysql+pymysql://"+db_admin+":"+db_password+"@localhost/"+db_name

engine = create_engine(create_engine_string, echo=True)

# Reflect an existing database into a new model
Base = automap_base()

Base.prepare(engine, reflect=True)

Study = Base.classes.studies
StudySampleAssociation = Base.classes.study_samples
ExpressionProfile = Base.classes.expression_profiles
OTUProfile = Base.classes.otu_profiles
ExpMicroCorrelation = Base.classes.expression_microbiome_correlations
ExpMicroCorrelationMethod = Base.classes.expression_microbiome_correlation_methods

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()

calculate_expression_metataxonomic_correlations(study_id, description_method, tool, stat_method,
                                                multiple_test_cor_method, rnaseq_norm, metatax_norm,
                                                correlation_cutoff, corrected_pvalue_cutoff)

session.close()