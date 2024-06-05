from flask import Blueprint, render_template, g, jsonify

from conekt import db, cache

from conekt.models.literature import LiteratureItem

from conekt.models.relationships.study_literature import StudyLiteratureAssociation
from conekt.models.seq_run import SeqRun
from conekt.models.studies import Study

study = Blueprint('study', __name__)

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