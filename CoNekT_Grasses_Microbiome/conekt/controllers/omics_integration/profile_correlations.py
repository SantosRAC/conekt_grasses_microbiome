from conekt import db
from flask import Blueprint, request, jsonify, render_template, Response

import json

from conekt import cache
from conekt.models.studies import Study
from conekt.models.expression_microbiome.expression_microbiome_correlation import\
    ExpMicroCorrelationMethod, ExpMicroCorrelation
from conekt.models.expression.profiles import ExpressionProfile
from conekt.models.microbiome.otu_profiles import OTUProfile
from conekt.models.species import Species

from conekt.helpers.chartjs import prepare_profiles_scatterplot

profile_correlations = Blueprint('profile_correlations', __name__)


@profile_correlations.route('/get_study_cor_methods/<study_id>/')
@profile_correlations.route('/get_study_cor_methods/<study_id>/<sample_group>/')
@cache.cached()
def get_study_cor_methods(study_id, sample_group):

    if not sample_group:
        sample_group = 'whole study'

    cor_methods = ExpMicroCorrelationMethod.query.filter_by(study_id=study_id,
                                                            sample_group=sample_group).all()

    methodArray = []
    cor_method_ids = []

    for method in cor_methods:
        cor_method_ids.append(method.id)
        methodObj = {}
        methodObj['id'] = method.id
        methodObj['method_tool'] = f'{method.stat_method} expression ({method.rnaseq_norm}) vs 16S ({method.metatax_norm}) - ({method.tool_name})'
        methodArray.append(methodObj)
    
    return jsonify({'methods': methodArray})


@profile_correlations.route('/get_study_cor_methods_two_studies/<study1_id>/<study2_id>/')
@cache.cached()
def get_study_cor_methods_two_studies(study1_id, study2_id):

    cor_methods_study1 = ExpMicroCorrelationMethod.query.filter_by(study_id=study1_id).all()
    cor_methods_study2 = ExpMicroCorrelationMethod.query.filter_by(study_id=study2_id).all()

    methodArray1 = []
    methodArray2 = []

    for method in cor_methods_study1:
        methodObj = {}
        methodObj['id'] = method.id
        methodObj['study_id'] = study1_id
        methodObj['method_tool'] = f'{method.stat_method} expression ({method.rnaseq_norm}) vs 16S ({method.metatax_norm}) - ({method.tool_name})'
        methodArray1.append(methodObj)
    
    for method in cor_methods_study2:
        methodObj = {}
        res = next((method_study1 for method_study1 in methodArray1 if method_study1['method_tool'] == f'{method.stat_method} expression ({method.rnaseq_norm}) vs 16S ({method.metatax_norm}) - ({method.tool_name})'), None)
        if res:
            methodObj['id'] = method.id
            methodObj['study_id'] = study2_id
            methodObj['method_tool'] = f'{method.stat_method} expression ({method.rnaseq_norm}) vs 16S ({method.metatax_norm}) - ({method.tool_name})'
            methodArray2.append(methodObj)
    
    return jsonify({'methods': methodArray2})


@profile_correlations.route('/get_correlated_profiles/<species_id>/<study_id>/<method_id>/<cutoff>/')
@cache.cached()
def get_correlated_profiles(species_id, study_id, method_id, cutoff):

    species = Species.query.get_or_404(species_id)
    study = Study.query.get_or_404(study_id)
    correlation_method = ExpMicroCorrelationMethod.query.get_or_404(method_id)

    results = ExpMicroCorrelation.query.\
        filter(ExpMicroCorrelation.exp_micro_correlation_method_id == method_id).\
        filter(ExpMicroCorrelation.corr_coef>=cutoff)

    return render_template("omics_integration/find_expression_microbiome_correlations.html",
                            results=results,
                            species=species,
                            study=study,
                            correlation_method=correlation_method)


@profile_correlations.route('/modal/profile_scatterplot/<expression_profile_id>/<metatax_profile_id>/')
@cache.cached()
def profiles_scatter_modal(expression_profile_id, metatax_profile_id):
    """
    Returns a scatterplot with correlations between two profiles in a modal

    :param 
    :return: 
    """
    
    expression_profile = ExpressionProfile.query.get_or_404(expression_profile_id)
    metatax_profile = OTUProfile.query.get_or_404(metatax_profile_id)

    plot = prepare_profiles_scatterplot(expression_profile, metatax_profile)

    return render_template('modals/expression_microbiome_profile_correlation.html',
                           expression_profile=expression_profile, metatax_profile=metatax_profile)


@profile_correlations.route('/json/profile_scatterplot/<expression_profile_id>/<metatax_profile_id>')
@cache.cached()
def profiles_scatter_modal_json(expression_profile_id, metatax_profile_id):
    """
    Generates a JSON object with  that can be rendered using Chart.js line plots
    """

    expression_profile = ExpressionProfile.query.get_or_404(expression_profile_id)
    metatax_profile = OTUProfile.query.get_or_404(metatax_profile_id)

    plot = prepare_profiles_scatterplot(expression_profile, metatax_profile)

    return Response(json.dumps(plot), mimetype='application/json')