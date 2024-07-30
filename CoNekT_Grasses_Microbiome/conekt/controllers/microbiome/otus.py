from flask import Blueprint, redirect, url_for, render_template, make_response, jsonify

from conekt import db, cache
from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit, OperationalTaxonomicUnitMethod
from conekt.models.relationships_microbiome.otu_classification import OTUClassificationMethod, OTUClassificationGG
from conekt.models.studies import Study
from conekt.models.microbiome.otu_profiles import OTUProfile
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

    taxonomy_associations = OTUClassificationMethod.get_otu_taxonomy(otu_id)

    return render_template('otu.html',
                           otu=current_otu,
                           otu_profiles=current_otu.otu_profiles,
                           taxonomy_associations=taxonomy_associations)

@otu.route('/modal/otu/<otu_id>')
def otu_modal(otu_id):
    """
    Returns the OTU sequence in a modal

    :param otu_id: ID of the OTU
    :return: Response with the fasta file
    """
    current_sequence = OperationalTaxonomicUnit.query\
        .get_or_404(otu_id)

    return render_template('modals/microbiome_sequence.html', sequence=current_sequence, otu=True)


@otu.route('/get_lit_otus/<literature_id>/')
@cache.cached()
def get_lit_otus(literature_id):
    """
    Returns a table with OTUs for the selected literature item (paper, book, book chapter)

    :param species_id: Internal ID of the species
    :param page: Page number
    """

    otu_methods = OperationalTaxonomicUnitMethod.query.filter_by(literature_id=int(literature_id)).all()

    outMethodArray = []

    for otu_method in otu_methods:
        outMethodObj = {}
        outMethodObj['id'] = otu_method.id
        outMethodObj['otu_method_summary']=f'{otu_method.description} ({otu_method.amplicon_marker}, {otu_method.clustering_method})'
        outMethodArray.append(outMethodObj)
    
    return jsonify({'otus': outMethodArray})


@otu.route('/download/otus/<study_id>')
def study_download_otus(study_id):
    """
    Generates a fasta file with all OTU representative sequences for a given study

    :param study_id: ID of the study
    :return: Response with the fasta file
    """
    output = []

    current_study = db.session.get(Study, study_id)
    otu_ids = db.session.execute(db.select(OTUProfile.__table__.c.otu_id).
                                  where(OTUProfile.__table__.c.study_id == current_study.id)).\
                                        fetchall()
    
    otu_ids = [otu_id[0] for otu_id in OTUProfile.query.with_entities(OTUProfile.otu_id).distinct().all()]
    otus = OperationalTaxonomicUnit.query.filter(OperationalTaxonomicUnit.id.in_(otu_ids)).all()

    for otu in otus:
        output.append(">" + otu.original_id)
        output.append(otu.representative_sequence)

    response = make_response("\n".join(output))
    response.headers["Content-Disposition"] = "attachment; filename=Study_" + str(current_study.id) + ".otus.fasta"
    response.headers['Content-type'] = 'text/plain'

    return response