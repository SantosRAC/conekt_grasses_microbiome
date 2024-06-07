from conekt import db

from flask import Blueprint, request, jsonify

from conekt import cache
from conekt.models.studies import Study
from conekt.models.expression_microbiome.expression_microbiome_correlation import\
    ExpMicroCorrelationMethod

profile_correlations = Blueprint('profile_correlations', __name__)


@profile_correlations.route('/get_study_cor_methods/<study_id>')
@cache.cached()
def get_study_cor_methods(study_id):

    cor_methods = ExpMicroCorrelationMethod.query.filter_by(study_id=study_id).all()

    methodArray = []
    cor_method_ids = []

    for method in cor_methods:
        cor_method_ids.append(method.id)
        methodObj = {}
        methodObj['id'] = method.id
        methodObj['method_tool'] = f'{method.stat_method} - ({method.tool_name})'
        methodArray.append(methodObj)
    
    return jsonify({'methods': methodArray})