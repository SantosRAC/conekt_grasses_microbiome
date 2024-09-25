from flask import render_template, request, Blueprint, jsonify
from conekt import db
from conekt.models.cluster import Cluster
from conekt.models.genome import Genome
from conekt.models.taxonomy import GTDBTaxon
from conekt.models.geographic_genomes_information import Geographic
from conekt.models.genome_envo import GenomeENVO
from conekt.models.ontologies import EnvironmentOntology
from conekt.models.genomes_quality import Genomes_quality
from conekt.models.literature import LiteratureItem
from conekt.models.ncbi_information import NCBI

search_page = Blueprint('search', __name__)

@search_page.route('/search', methods=['GET', 'POST'])
def search():
    results = []

    if request.method == 'POST':
        # Captura os dados do formulário
        taxonomy = request.form.get('taxonomy')
        country = request.form.get('country')
        envo_class = request.form.get('envo_class')
        envo_annotation = request.form.get('envo_annotation')

        # Monta a consulta dinâmica
        query = db.session.query(
            Genome.genome_id,
            Genome.genome_type,
            GTDBTaxon.taxon_path,
            Genomes_quality.quality,
            Geographic.country,
            Geographic.local,
            EnvironmentOntology.envo_class,
            EnvironmentOntology.envo_annotation,
            LiteratureItem.doi,
            NCBI.ncbi_accession,
            Cluster.id.label('cluster_id')  # Incluir o cluster_id
        ).outerjoin(Cluster, Genome.cluster_id == Cluster.id) \
         .outerjoin(GTDBTaxon, Cluster.gtdb_id == GTDBTaxon.id) \
         .outerjoin(Genomes_quality, Genome.genome_id == Genomes_quality.genome_id) \
         .outerjoin(Geographic, Genome.genome_id == Geographic.genome_id) \
         .outerjoin(GenomeENVO, Genome.genome_id == GenomeENVO.genome_id) \
         .outerjoin(EnvironmentOntology, GenomeENVO.envo_habitat == EnvironmentOntology.envo_term) \
         .outerjoin(LiteratureItem, Genome.literature_id == LiteratureItem.id) \
         .outerjoin(NCBI, Genome.genome_id == NCBI.genome_id)

        # Adiciona os filtros de acordo com os parâmetros de busca
        if taxonomy:
            query = query.filter(GTDBTaxon.taxon_path.like(f"%{taxonomy}%"))
        if country:
            query = query.filter(Geographic.country.like(f"%{country}%"))
        if envo_class:
            query = query.filter(EnvironmentOntology.envo_class.like(f"%{envo_class}%"))
        if envo_annotation:
            query = query.filter(EnvironmentOntology.envo_annotation.like(f"%{envo_annotation}%"))

        # Executa a consulta e armazena os resultados
        results = query.all()

    return render_template('search.html', results=results)


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
