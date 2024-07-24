from flask import Blueprint, render_template, g, make_response, Response, flash, jsonify
from markdown import markdown

from conekt import db, cache
from conekt.models.species import Species
from conekt.models.literature import LiteratureItem
from conekt.models.seq_run import SeqRun
from conekt.models.relationships.sample_literature import SampleLitAssociation
from conekt.models.sequences import Sequence
from conekt.models.clades import Clade

from sqlalchemy.orm import undefer, noload
from sqlalchemy import desc

species = Blueprint('species', __name__)


@species.route('/')
@cache.cached()
def species_overview():
    """
    Overview of all species with data in the current database, including some basic statistics

    Pulls the largest clade defined in Clades from the database (if present) and adds this as the tree to the page
    """
    all_species = Species.query.all()

    largest_clade = Clade.query.order_by(desc(Clade.species_count)).limit(1).first()

    tree = largest_clade.newick_tree_species if largest_clade is not None else None

    # adding variable to get Literature from DB
    #literature_info = LiteratureItem.query.all()

    # For each species query the literature table and add the literature info to the species object
    for species in all_species:
        if LiteratureItem.query.filter_by(id=species.literature_id).first():
            species.paper_author_names = LiteratureItem.query.filter_by(id=species.literature_id).first().author_names
            species.paper_public_year = LiteratureItem.query.filter_by(id=species.literature_id).first().public_year
            species.paper_doi = LiteratureItem.query.filter_by(id=species.literature_id).first().doi
        

    return render_template('species.html', all_species=all_species, species_tree=tree)


@species.route('/view/<species_id>')
@cache.cached()
def species_view(species_id):
    """
    Get a species based on the ID and show the details for this species. The description, which can be markdown is
    converted prior to adding it to the template.

    :param species_id: ID of the species to show
    """
    current_species = db.session.get(Species, species_id)

    if not current_species.has_cazyme:
        flash('No <strong>CAZyme domains</strong> present in the database for this species', 'warning')

    if not current_species.has_interpro:
        flash('No <strong>InterPro domains</strong> present in the database for this species', 'warning')

    if not current_species.has_go:
        flash('No <strong>GO annotation</strong> present in the database for this species', 'warning')

    description = None if current_species.description is None \
        else markdown(current_species.description, extensions=['markdown.extensions.tables', 'markdown.extensions.attr_list'])

    return render_template('species.html', species=current_species, description=description)


@species.route('/sequences/<species_id>/')
@species.route('/sequences/<species_id>/<int:page>')
@cache.cached()
def species_sequences(species_id, page=1):
    """
    Returns a table with sequences from the selected species

    :param species_id: Internal ID of the species
    :param page: Page number
    """
    sequences = db.session.get(Species, species_id).sequences.paginate(page=page,
                                                                 per_page=g.page_items,
                                                                 error_out=False).items

    return render_template('pagination/sequences.html', sequences=sequences)


@species.route('/get_run_papers/<species_id>/<run_data_type>/')
@cache.cached()
def get_run_papers(species_id, run_data_type, page=1):
    """
    Returns a table with literature items from RNA-seq or metataxonomics runs for the selected species

    :param species_id: Internal ID of the species
    :param run_data_type: Type of data to show (rnaseq or metataxonomics)
    :param page: Page number
    """

    lit_info = SeqRun.query.with_entities(SeqRun.literature_id).filter_by(species_id=species_id,
                                                                          data_type=run_data_type).distinct().all()

    literatures = LiteratureItem.query.filter(LiteratureItem.id.in_([lit_id[0] for lit_id in lit_info]))

    litArray = []

    for literature in literatures:
        litObj = {}
        litObj['id'] = literature.id
        if literature.qtd_author > 1:
            litObj['publication_detail'] = f'{literature.author_names} et al. ({literature.public_year})'
        else:
            litObj['publication_detail'] = f'{literature.author_names} ({literature.public_year})'
        litArray.append(litObj)
    
    return jsonify({'literatures': litArray})


@species.route('/download/coding/<species_id>')
def species_download_coding(species_id):
    """
    Generates a fasta file with all coding sequences for a given species

    :param species_id: Internal ID of the species
    :return: Response with the fasta file
    """
    output = []

    current_species = db.session.get(Species, species_id)
    sequences = db.session.execute(db.select(Sequence.__table__.c.name, Sequence.__table__.c.coding_sequence).
                                  where(Sequence.__table__.c.type == 'protein_coding',
                                        Sequence.__table__.c.species_id == current_species.id)).\
                                        fetchall()

    for (name, coding_sequence) in sequences:
        output.append(">" + name)
        output.append(coding_sequence)

    response = make_response("\n".join(output))
    response.headers["Content-Disposition"] = "attachment; filename=" + current_species.code + ".cds.fasta"
    response.headers['Content-type'] = 'text/plain'

    return response


@species.route('/download/protein/<species_id>')
def species_download_protein(species_id):
    """
    Generates a fasta file with all amino acid sequences for a given species

    :param species_id: Internal ID of the species
    :return: Response with the fasta file
    """
    output = []

    current_species = db.session.get(Species, species_id)
    sequences = (
        current_species.sequences.where(Sequence.type == 'protein_coding')
        .options(undefer(Sequence.coding_sequence))
        .options(noload(Sequence.xrefs))
        .all()
    )

    for s in sequences:
        output.append(">" + s.name)
        output.append(s.protein_sequence)

    response = make_response("\n".join(output))
    response.headers["Content-Disposition"] = "attachment; filename=" + current_species.code + ".aa.fasta"
    response.headers['Content-type'] = 'text/plain'

    return response

#dowload rna fasta -----------------------------------------------
@species.route('/download/rna/<species_id>')
def species_download_rna(species_id):
    """
    Generates a fasta file with all rna sequences for a given species

    :param species_id: Internal ID of the species
    :return: Response with the fasta file
    """
    output = []

    current_species = db.session.get(Species, species_id)
    sequences = db.session.execute(db.select(Sequence.__table__.c.name, Sequence.__table__.c.coding_sequence).
                                  where(Sequence.__table__.c.type == 'RNA',
                                        Sequence.__table__.c.species_id == current_species.id)).\
                                        fetchall()

    for (name, coding_sequence) in sequences:
        output.append(">" + name)
        output.append(coding_sequence)

    response = make_response("\n".join(output))
    response.headers["Content-Disposition"] = "attachment; filename=" + current_species.code + ".rna.fasta"
    response.headers['Content-type'] = 'text/plain'

    return response


@species.route('/stream/coding/<species_id>')
def species_stream_coding(species_id):
    """
    Generates a fasta file with all coding sequences for a given species. However this is send as a streaming
    response (and seems to bring up the download dialog a few seconds faster)

    :param species_id: Internal ID of the species
    :return: Streamed response with the fasta file
    """
    def generate(selected_species):
        current_species = db.session.get(Species, selected_species)
        sequences = db.session.execute(db.select(Sequence.__table__.c.name, Sequence.__table__.c.coding_sequence).
                                  where(Sequence.__table__.c.type == 'protein_coding',
                                        Sequence.__table__.c.species_id == current_species.id)).\
                                        fetchall()

        for name, coding_sequence in sequences:
            yield ">" + name + '\n' + coding_sequence + '\n'

    return Response(generate(species_id), mimetype='text/plain')


@species.route('/stream/protein/<species_id>')
def species_stream_protein(species_id):
    """
    Generates a fasta file with all amino acid sequences for a given species. However this is send as a streaming
    response (and seems to bring up the download dialog a few seconds faster)

    :param species_id: Internal ID of the species
    :return: Streamed response with the fasta file
    """
    def generate(selected_species):
        current_species = db.session.get(Species, selected_species)
        sequences = (
            current_species.sequences.where(Sequence.type == 'protein_coding')
            .options(undefer(Sequence.coding_sequence))
            .options(noload(Sequence.xrefs))
            .all()
        )

        for s in sequences:
            yield ">" + s.name + '\n' + s.protein_sequence + '\n'

    return Response(generate(species_id), mimetype='text/plain')

#stream rna fasta -----------------------------------------------
@species.route('/stream/rna/<species_id>')
def species_stream_rna(species_id):
    """
    Generates a fasta file with all RNA sequences for a given species. However this is send as a streaming
    response (and seems to bring up the download dialog a few seconds faster)

    :param species_id: Internal ID of the species
    :return: Streamed response with the fasta file
    """
    def generate(selected_species):
        current_species = db.session.get(Species, selected_species)
        sequences = db.session.execute(db.select(Sequence.__table__.c.name, Sequence.__table__.c.coding_sequence).
                                  where(Sequence.__table__.c.type == 'RNA',
                                        Sequence.__table__.c.species_id == current_species.id)).\
                                        fetchall()

        for name, coding_sequence in sequences:
            yield ">" + name + '\n' + coding_sequence + '\n'

    return Response(generate(species_id), mimetype='text/plain')



