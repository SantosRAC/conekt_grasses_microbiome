from flask import Blueprint, redirect, url_for, render_template, make_response

from conekt import cache
from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit
from sqlalchemy.orm import undefer, noload

otu = Blueprint('otu', __name__)


@otu.route('/')
def otu_overview():
    """
    For lack of a better alternative redirect users to the main page
    """
    return redirect(url_for('main.screen'))


@otu.route('/find/<otu_original_id>')
@cache.cached()
def otu_find(otu_original_id):
    """
    Find a OTU based on the name and show the details (useful for incoming links from other platforms)

    :param sequence_name: Name of the OTU (original_id)
    """
    current_otu = OperationalTaxonomicUnit.query.filter_by(original_id=otu_original_id).first_or_404()

    return redirect(url_for('otu.otu_view', sequence_id=current_otu.id))


@otu.route('/view/<otu_id>')
@cache.cached()
def otu_view(otu_id):
    """
    Get a OTU based on the ID and show its details

    :param sequence_id: ID of the OTU
    """
    #TODO: Import the necessary classes (taxonomic information, representative sequence, etc.)

    current_otu = OperationalTaxonomicUnit.query.get_or_404(otu_id)

    # to avoid running long count queries, fetch relations here and pass to template
    #expression_profiles=current_sequence.expression_profiles.all()
    return render_template('otu.html',
                           otu=current_otu,
                           otu_profiles=current_otu.otu_profiles.all()
                           )