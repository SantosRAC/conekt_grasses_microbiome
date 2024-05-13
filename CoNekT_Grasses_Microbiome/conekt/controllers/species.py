from flask import Blueprint, render_template, g, make_response, Response, flash
from markdown import markdown

from conekt import db, cache
from conekt.models.species import Species
from conekt.models.literature import LiteratureItem
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
    current_species = db.session.query.get_or_404(Species, species_id)

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


@species.route('/expression_papers/<species_id>/')
@species.route('/expression_papers/<species_id>/<int:page>')
@cache.cached()
def species_expression_papers(species_id, page=1):
    """
    Returns a table with literature items from RNA-seq for the selected species

    :param species_id: Internal ID of the species
    :param page: Page number
    """

    lit_info = SampleLitAssociation.query.with_entities(SampleLitAssociation.literature_id).filter_by(species_id=species_id).distinct().all()

    literatures = LiteratureItem.query.filter(LiteratureItem.id.in_([lit_id[0] for lit_id in lit_info])).paginate(page,
                                                                 g.page_items,
                                                                 False).items

    return render_template('pagination/literatures.html', literatures=literatures)


@species.route('/microbiome_papers/<species_id>/')
@species.route('/microbiome_papers/<species_id>/<int:page>')
@cache.cached()
def species_microbiome_papers(species_id, page=1):
    """
    Returns a table with literature items from microbiome data for the selected species

    :param species_id: Internal ID of the species
    :param page: Page number
    """

    lit_info = SampleLitAssociation.query.with_entities(SampleLitAssociation.literature_id).filter_by(species_id=species_id).distinct().all()

    literatures = LiteratureItem.query.filter(LiteratureItem.id.in_([lit_id[0] for lit_id in lit_info])).paginate(page,
                                                                 g.page_items,
                                                                 False).items

    return render_template('pagination/literatures.html', literatures=literatures)


@species.route('/download/coding/<species_id>')
def species_download_coding(species_id):
    """
    Generates a fasta file with all coding sequences for a given species

    :param species_id: Internal ID of the species
    :return: Response with the fasta file
    """
    output = []

    current_species = db.session.get(Species, species_id)
    sequences = db.engine.execute(db.select([Sequence.__table__.c.name, Sequence.__table__.c.coding_sequence]).
                                  where(Sequence.__table__.c.species_id == current_species.id)).\
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
    sequences = current_species.sequences.options(undefer('coding_sequence')).options(noload('xrefs')).all()

    for s in sequences:
        if s.type == "protein_coding":
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
    sequences = db.engine.execute(db.select([Sequence.__table__.c.name, Sequence.__table__.c.coding_sequence,
                                             Sequence.__table__.c.type]).
                                  where(Sequence.__table__.c.species_id == current_species.id)).\
        fetchall()

    for (name, coding_sequence, type) in sequences:
        if type == "RNA":
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
        sequences = db.engine.execute(db.select([Sequence.__table__.c.name, Sequence.__table__.c.coding_sequence, Sequence.__table__.c.type]).
                                      where(Sequence.__table__.c.species_id == selected_species)).\
            fetchall()

        for name, coding_sequence, type in sequences:
            if type == 'protein_coding':
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
    import time

    def generate(selected_species):
        
        sequences = []
        limit = 15000
        offset = 0

        counting_rows = Sequence.query\
                .options(undefer('coding_sequence'))\
                .options(noload('xrefs'))\
                .filter_by(species_id=selected_species)\
                .filter_by(type='protein_coding')\
                .count()

        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time

            rows = Sequence.query\
                .options(undefer('coding_sequence'))\
                .options(noload('xrefs'))\
                .filter_by(species_id=selected_species)\
                .filter_by(type='protein_coding')\
                .limit(limit)\
                .offset(offset)

            if (limit + offset) >= counting_rows:
                sequences.extend(rows)
                perc_recovered = (len(sequences) / counting_rows) * 100
                print("Size of current rows in sequences: " + str(len(sequences)) + "(Perc: " + str(perc_recovered) + "%)")
                time.sleep(1)
                break
            else:
                sequences.extend(rows)
                print("Size of current rows in sequences: " + str(len(sequences)))
                perc_recovered = (len(sequences) / counting_rows) * 100
                print("Size of current rows in sequences: " + str(len(sequences)) + "(Perc: " + str(perc_recovered) + "%)")
                time.sleep(1)

            if (offset + limit) <= counting_rows:
                offset += limit
                print("Total proteins: ", counting_rows, "Limit: ", limit, "Offset: ", offset)
                perc_recovered = (len(sequences) / counting_rows) * 100
                print("Size of current rows in sequences: " + str(len(sequences)) + "(Perc: " + str(perc_recovered) + "%)")
                print(f"Elapsed time: {elapsed_time:.2f} seconds")
                time.sleep(1)

        for s in sequences:
            if s.type == "protein_coding":
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
        sequences = db.engine.execute(db.select([Sequence.__table__.c.name, Sequence.__table__.c.coding_sequence, Sequence.__table__.c.type]).
                                      where(Sequence.__table__.c.species_id == selected_species)).\
            fetchall()

        for name, coding_sequence, type in sequences:
            if type == 'RNA':
                yield ">" + name + '\n' + coding_sequence + '\n'

    return Response(generate(species_id), mimetype='text/plain')



