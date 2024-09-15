from flask import Blueprint, redirect, url_for, render_template, make_response, jsonify

from conekt import db, cache
from conekt.models.microbiome.asvs import AmpliconSequenceVariantMethod

asv = Blueprint('asv', __name__)

@asv.route('/get_lit_asvs/<literature_id>/')
@cache.cached()
def get_lit_asvs(literature_id):
    """
    Returns a table with ASVs for the selected literature item (paper, book, book chapter)

    :param species_id: Internal ID of the species
    :param page: Page number
    """

    asv_methods = AmpliconSequenceVariantMethod.query.filter_by(literature_id=int(literature_id)).all()

    asvMethodArray = []

    for asv_method in asv_methods:
        asvMethodObj = {}
        asvMethodObj['id'] = asv_method.id
        asvMethodObj['asv_method_summary']=f'{asv_method.description} ({asv_method.amplicon_marker})'
        asvMethodArray.append(asvMethodObj)
    
    return jsonify({'asvs': asvMethodArray})