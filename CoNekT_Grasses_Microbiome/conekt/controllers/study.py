from flask import Blueprint, render_template, g, jsonify
from markdown import markdown

from conekt import db, cache

from conekt.models.literature import LiteratureItem

from conekt.models.relationships.study_literature import StudyLiteratureAssociation
from conekt.models.relationships.study_sample import StudySampleAssociation
from conekt.models.relationships.sample_group import SampleGroupAssociation
from conekt.models.microbiome.operational_taxonomic_unit import\
                    OperationalTaxonomicUnitMethod, OperationalTaxonomicUnit
from conekt.models.species import Species
from conekt.models.seq_run import SeqRun
from conekt.models.studies import Study
from conekt.models.microbiome.specificity import MicrobiomeSpecificityMethod

study = Blueprint('study', __name__)


@study.route('/')
@cache.cached()
def studies_overview():
    """
    Overview of all studies with data in the current database, including some basic statistics
    """
    all_studies = Study.query.all()

    study_species_ids = Study.query.with_entities(Study.species_id).distinct()
    study_species = Species.query.filter(Species.id.in_([species_id[0] for species_id in study_species_ids])).all()
    species_dict = {species.id: species.name for species in study_species}

    return render_template('study.html', all_studies=all_studies, species_dict=species_dict)


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

@study.route('/krona/<study_id>')
@cache.cached()
def study_krona(study_id):
    """
    Get a study based on the ID and show the Krona plot.

    :param study_id: ID of the study to show
    """
    current_study = db.session.get(Study, study_id)

    krona_html = current_study.krona_html

    return render_template('study/krona.html', krona_html=krona_html, current_study=current_study)

@study.route('/expression_pca/<study_id>')
@cache.cached()
def expression_pca_plot(study_id):
    """
    Get a study based on the ID and show the PCA plot.

    :param study_id: ID of the study to show
    """
    current_study = db.session.get(Study, study_id)

    return render_template('study/expression_pca.html', current_study=current_study)


@study.route('/metatax_pca/<study_id>')
@cache.cached()
def metatax_pca_plot(study_id):
    """
    Get a study based on the ID and show the PCA plot.

    :param study_id: ID of the study to show
    """
    current_study = db.session.get(Study, study_id)

    return render_template('study/metatax_pca.html', current_study=current_study)


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
@study.route('/get_species_studies/<species_id>/')
@cache.cached()
def get_species_studies(species_id, study_type=None):

    if study_type:
        studies = Study.query.with_entities(Study.id, Study.name).filter_by(species_id=species_id, data_type=study_type).all()
    else:
        studies = Study.query.with_entities(Study.id, Study.name).filter_by(species_id=species_id).all()

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


@study.route('/get_specificity_conditions/<study_id>')
@cache.cached()
def get_specificity_methods(study_id):

    study_specificity_methods = MicrobiomeSpecificityMethod.query.with_entities(MicrobiomeSpecificityMethod.id,
                                                                                MicrobiomeSpecificityMethod.description,
                                                                                MicrobiomeSpecificityMethod.study_id).\
        where(MicrobiomeSpecificityMethod.study_id==study_id).all()

    specMethodArray = []
    spec_method_ids = []

    for spec_method in study_specificity_methods:
        if spec_method.id in spec_method_ids:
            continue
        else:
            spec_method_ids.append(spec_method.id)
        specMethodsObj = {}
        specMethodsObj['id'] = spec_method.id
        specMethodsObj['description'] = f'{spec_method.description}'
        specMethodArray.append(specMethodsObj)
    
    return jsonify({'specificity_methods': specMethodArray})


@study.route('/get_sample_group_names/<study_id>')
@cache.cached()
def get_sample_group_names(study_id):

    sample_ids = StudySampleAssociation.query.with_entities(StudySampleAssociation.sample_id).\
        where(StudySampleAssociation.study_id==study_id).distinct().all()

    groups = SampleGroupAssociation.query.with_entities(SampleGroupAssociation.group_type,
                                                        SampleGroupAssociation.group_name).\
                                filter(SampleGroupAssociation.sample_id.in_([sample_id[0] for sample_id in sample_ids])).\
                                    distinct().all()

    sampleGroupArray = []

    for group_info in groups:
        groupTObj = {}
        groupTObj['group_name'] = group_info.group_name
        groupTObj['group_type'] = group_info.group_type
        sampleGroupArray.append(groupTObj)
    
    return jsonify({'sample_group_names': sampleGroupArray})