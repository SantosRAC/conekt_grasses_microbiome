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
        
        session.add(new_correlation_method)
        session.commit()

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
                session.add(new_correlation_pair)

                if i % 400 == 0:
                    session.commit()

        session.commit()

        # Return the calculated correlations
        return True

db_admin = args.db_admin
db_name = args.db_name

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

calculate_expression_metataxonomic_correlations()

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()