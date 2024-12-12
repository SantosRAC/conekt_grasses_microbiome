from flask import render_template, request, Blueprint, jsonify
from conekt import db
from conekt.models.cluster import Cluster
from conekt.models.genome import Genome
from conekt.models.taxonomy import GTDBTaxon
from conekt.models.geographic_genomes_information import Geographic
from conekt.models.genome_envo import GenomeENVO
from conekt.models.ontologies import EnvironmentOntology
from conekt.models.genomes_quality import GenomesQuality
from conekt.models.literature import LiteratureItem
from conekt.models.ncbi_information import NCBI
from flask_whooshee import WhoosheeQuery

from conekt.forms.search import BasicSearchForm

search_page = Blueprint('search', __name__)

@search_page.route('/search', methods=['GET', 'POST'])
def search():
    print("oi")
    results = []
    form = BasicSearchForm(request.form)

    if request.method == 'POST':
        taxonomy = request.form.get('taxonomy')
        country = request.form.get('country')
        envo_class = request.form.get('envo_class')
        envo_annotation = request.form.get('envo_annotation')
        
        print(taxonomy, country, envo_class, envo_annotation)

        # Executar busca para cada parâmetro, se fornecido
        if taxonomy:
            taxonomy_results = Genome.query.whooshee_search(taxonomy).all()
            results.extend(taxonomy_results)

        if country:
            country_results = Geographic.query.whooshee_search(country).all()
            results.extend(country_results)

        if envo_class:
            envo_class_results = EnvironmentOntology.query.whooshee_search(envo_class).all()
            results.extend(envo_class_results)

        if envo_annotation:
            envo_annotation_results = EnvironmentOntology.query.whooshee_search(envo_annotation).all()
            results.extend(envo_annotation_results)


    return render_template('search.html', results=results, form=form)


# Rota para buscar country (para preenchimento automático)
@search_page.route('/get_country')
def get_country():
    countries = db.session.query(Geographic.country).distinct().all()
    country_list = [country[0] for country in countries if country[0]]
    return jsonify(country_list)

# Rota para buscar ENVO Class (para preenchimento automático)
@search_page.route('/get_envo_classes')
def get_envo_classes():
    envo_classes = db.session.query(EnvironmentOntology.envo_class).distinct().all()
    envo_classes_list = [envo_class[0] for envo_class in envo_classes if envo_class[0]]
    return jsonify(envo_classes_list)

# Rota para buscar ENVO Annotation (para preenchimento automático)
@search_page.route('/get_envo_annotations')
def get_envo_annotations():
    envo_annotations = db.session.query(EnvironmentOntology.envo_annotation).distinct().all()
    envo_annotations_list = [envo_annotation[0] for envo_annotation in envo_annotations if envo_annotation[0]]
    return jsonify(envo_annotations_list)
