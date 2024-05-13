from flask import Blueprint, redirect, url_for, render_template, make_response

from conekt import cache
from conekt.models.sequences import Sequence
from sqlalchemy.orm import undefer, noload

sequence = Blueprint('sequence', __name__)


@sequence.route('/')
def sequence_overview():
    """
    For lack of a better alternative redirect users to the main page
    """
    return redirect(url_for('main.screen'))


@sequence.route('/find/<sequence_name>')
@cache.cached()
def sequence_find(sequence_name):
    """
    Find a sequence based on the name and show the details for this sequence (useful for incoming links from other
    platforms)

    :param sequence_name: Name of the sequence
    """
    current_sequence = Sequence.query.filter_by(name=sequence_name).first_or_404()

    return redirect(url_for('sequence.sequence_view', sequence_id=current_sequence.id))


@sequence.route('/view/<sequence_id>')
@cache.cached()
def sequence_view(sequence_id):
    """
    Get a sequence based on the ID and show the details for this sequence

    :param sequence_id: ID of the sequence
    """
    from conekt.models.relationships.sequence_go import SequenceGOAssociation
    from conekt.models.relationships.sequence_cazyme import SequenceCAZYmeAssociation

    current_sequence = Sequence.query.get_or_404(sequence_id)

    go_associations = current_sequence.go_associations.group_by(SequenceGOAssociation.go_id,
                                                                SequenceGOAssociation.evidence,
                                                                SequenceGOAssociation.source).all()
    
    cazyme_associations = current_sequence.cazyme_associations.group_by(SequenceCAZYmeAssociation.cazyme_id).all()

    # to avoid running long count queries, fetch relations here and pass to template
    #expression_profiles=current_sequence.expression_profiles.all()
    return render_template('sequence.html',
                           sequence=current_sequence,
                           go_associations=go_associations,
                           interpro_associations=current_sequence.interpro_associations.all(),
                           cazyme_associations=cazyme_associations,
                           families=current_sequence.families.all(),
                           expression_profiles=current_sequence.expression_profiles.all(),
                           network_nodes=current_sequence.network_nodes.all(),
                           coexpression_clusters=current_sequence.coexpression_clusters.all(),
                           ecc_query_associations=current_sequence.ecc_query_associations.all()
                           )


@sequence.route('/tooltip/<sequence_id>')
@cache.cached()
def sequence_tooltip(sequence_id):
    """
    Get a sequence based on the ID and show the details for this sequence

    :param sequence_id: ID of the sequence
    """
    current_sequence = Sequence.query.get_or_404(sequence_id)

    return render_template('tooltips/sequence.html', sequence=current_sequence)


@sequence.route('/modal/coding/<sequence_id>/<rna>')
def sequence_modal_coding(sequence_id, rna):
    """
    Returns the coding sequence in a modal

    :param sequence_id: ID of the sequence
    :return: Response with the fasta file
    """
    current_sequence = Sequence.query\
        .options(undefer('coding_sequence'))\
        .options(noload('xrefs'))\
        .get_or_404(sequence_id)
    
    name = current_sequence.name

    if rna == 'true':
        current_sequence = Sequence.query\
            .filter_by(name=name, type='RNA')\
            .options(undefer('coding_sequence'))\
            .options(noload('xrefs'))\
            .first()

    return render_template('modals/sequence.html', sequence=current_sequence, coding=True)


@sequence.route('/modal/protein/<sequence_id>')
def sequence_modal_protein(sequence_id):
    """
    Returns the protein sequence in a modal

    :param sequence_id: ID of the sequence
    :return: Response with the fasta file
    """
    current_sequence = Sequence.query\
        .options(undefer('coding_sequence'))\
        .options(noload('xrefs'))\
        .get_or_404(sequence_id)

    return render_template('modals/sequence.html', sequence=current_sequence, coding=False)


@sequence.route('/fasta/coding/<sequence_id>/<rna>')
def sequence_fasta_coding(sequence_id, rna):
    """
    Returns the coding sequence as a downloadable fasta file

    :param sequence_id: ID of the sequence
    :return: Response with the fasta file
    """

    current_sequence = Sequence.query\
        .options(undefer('coding_sequence'))\
        .options(noload('xrefs'))\
        .get_or_404(sequence_id)

    name = current_sequence.name

    if rna == 'true':
        current_sequence = Sequence.query\
            .filter_by(name=name, type='RNA')\
            .options(undefer('coding_sequence'))\
            .options(noload('xrefs'))\
            .first()

    fasta = ">" + current_sequence.name + "\n" + current_sequence.coding_sequence + "\n"
    response = make_response(fasta)
    response.headers["Content-Disposition"] = "attachment; filename=" + current_sequence.name + ".cds.fasta"
    response.headers['Content-type'] = 'text/plain'

    return response


@sequence.route('/fasta/protein/<sequence_id>')
def sequence_fasta_protein(sequence_id):
    """
    Returns the protein sequence as a downloadable fasta file

    :param sequence_id: ID of the sequence
    :return: Response with the fasta file
    """
    current_sequence = Sequence.query\
        .options(undefer('coding_sequence'))\
        .options(noload('xrefs'))\
        .get_or_404(sequence_id)

    fasta = ">" + current_sequence.name + "\n" + current_sequence.protein_sequence + "\n"
    response = make_response(fasta)
    response.headers["Content-Disposition"] = "attachment; filename=" + current_sequence.name + ".protein.fasta"
    response.headers['Content-type'] = 'text/plain'

    return response
