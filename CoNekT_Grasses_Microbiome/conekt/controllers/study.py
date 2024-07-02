from flask import Blueprint, render_template, g, jsonify
from markdown import markdown

from conekt import db, cache

from conekt.models.literature import LiteratureItem

from conekt.models.relationships.study_literature import StudyLiteratureAssociation
#from conekt.models.microbiome.operational_taxonomic_unit import\
#                    OperationalTaxonomicUnitMethod, OperationalTaxonomicUnit
from conekt.models.seq_run import SeqRun
from conekt.models.studies import Study

study = Blueprint('study', __name__)


@study.route('/')
@cache.cached()
def studies_overview():
    """
    Overview of all studies with data in the current database, including some basic statistics
    """
    all_studies = Study.query.all()

    '''for species in all_species:
        if LiteratureItem.query.filter_by(id=species.literature_id).first():
            species.paper_author_names = LiteratureItem.query.filter_by(id=species.literature_id).first().author_names
            species.paper_public_year = LiteratureItem.query.filter_by(id=species.literature_id).first().public_year
            species.paper_doi = LiteratureItem.query.filter_by(id=species.literature_id).first().doi
    '''    

    return render_template('study.html', all_studies=all_studies)


@study.route('/view/<study_id>')
@cache.cached()
def study_view(study_id):
    """
    Get a study based on the ID and show the details for this study.

    :param study_id: ID of the study to show
    """
    current_study = db.session.get(Study, study_id)

    description = None if current_study.description is None \
        else markdown(current_study.description, extensions=['markdown.extensions.tables', 'markdown.extensions.attr_list'])

    return render_template('study.html', study=current_study, description=description)
    


@study.route('/studies_papers/<study_id>/')
@study.route('/studies_papers/<study_id>/<int:page>')
@cache.cached()
def study_papers(study_id, page=1):
    """
    Returns a table with literature items from the selected study

    :param study_id: Internal ID of the study
    :param page: Page number
    """

    lit_info = StudyLiteratureAssociation.query.with_entities(StudyLiteratureAssociation.literature_id).filter_by(study_id=study_id).distinct().all()

    literatures = LiteratureItem.query.filter(LiteratureItem.id.in_([lit_id[0] for lit_id in lit_info])).paginate(page=page,
                                                                 per_page=g.page_items,
                                                                 error_out=False).items

    return render_template('pagination/literatures.html', literatures=literatures)


@study.route('/species_studies/<species_id>/<study_type>/')
@study.route('/species_studies/<species_id>/<study_type>/<int:page>')
@cache.cached()
def species_studies(species_id, study_type, page=1):
    """
    Returns a table with studies from the selected species and study type

    :param species_id: Internal ID of the species
    :param study_type: Type of the study
    :param page: Page number
    """

    studies = Study.query.filter_by(species_id=species_id, data_type=study_type).paginate(page=page,
                                                                 per_page=g.page_items,
                                                                 error_out=False).items

    return render_template('pagination/studies.html', studies=studies)


@study.route('/otus/<study_id>/')
@study.route('/otus/<study_id>/<int:page>')
@cache.cached()
def study_otus(study_id, page=1):
    """
    Returns a table with OTUs from the selected study

    :param study_id: Internal ID of the study
    :param page: Page number
    """

    lit_info = StudyLiteratureAssociation.query.with_entities(StudyLiteratureAssociation.literature_id).filter_by(study_id=study_id).distinct().all()

    otu_methods = OperationalTaxonomicUnitMethod.query.with_entities(OperationalTaxonomicUnitMethod.id).filter(OperationalTaxonomicUnitMethod.literature_id.in_([lit_id[0] for lit_id in lit_info])).all()

    otus = OperationalTaxonomicUnit.query.filter(OperationalTaxonomicUnit.method_id.in_([method_id[0] for method_id in otu_methods])).paginate(page=page,
                                                                 per_page=g.page_items,
                                                                 error_out=False).items

    return render_template('pagination/otus.html', otus=otus)


@study.route('/get_species_lits_with_runs/<species_id>/<study_type>')
@cache.cached()
def get_species_lits_with_runs(species_id, study_type):
    
    if study_type == 'expression_metataxonomics':
        lit_info = SeqRun.query.with_entities(SeqRun.literature_id).filter_by(species_id=species_id).distinct().all()
    else:
        lit_info = SeqRun.query.with_entities(SeqRun.literature_id).filter_by(species_id=species_id, data_type=study_type).distinct().all()

    literatureArray = []
    literature_ids = []

    for lit_id in lit_info:
        lit_author = LiteratureItem.query.get(lit_id).author_names
        lit_year = LiteratureItem.query.get(lit_id).public_year
        literature_id = LiteratureItem.query.get(lit_id).id
        if lit_id in literature_ids:
            continue
        else:
            literature_ids.append(literature_id)
        litObj = {}
        litObj['id'] = literature_id
        litObj['publication_detail'] = f'{lit_author} ({lit_year})'
        literatureArray.append(litObj)
    
    return jsonify({'literatures': literatureArray})


@study.route('/get_species_studies/<species_id>/<study_type>')
@cache.cached()
def get_species_studies(species_id, study_type):

    studies = Study.query.with_entities(Study.id, Study.name).filter_by(species_id=species_id, data_type=study_type).all()

    studyArray = []
    study_ids = []

    for study in studies:
        if study.id in study_ids:
            continue
        else:
            study_ids.append(study.id)
        studyObj = {}
        studyObj['id'] = study.id
        studyObj['name'] = f'{study.name}'
        studyArray.append(studyObj)
    
    return jsonify({'studies': studyArray})