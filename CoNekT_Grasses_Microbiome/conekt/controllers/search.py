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
    results = []
    form = BasicSearchForm(request.form)

    if request.method == 'POST':
        taxonomy = request.form.get('taxonomy')
        country = request.form.get('country')
        envo_class = request.form.get('envo_class')
        envo_annotation = request.form.get('envo_annotation')

        genome_ids = set()

        if taxonomy:
            taxonomy_results = GTDBTaxon.query.whooshee_search(taxonomy).all()
            gtdb_ids = [taxon.id for taxon in taxonomy_results] 

            if gtdb_ids:
                cluster_results = Cluster.query.filter(Cluster.gtdb_id.in_(gtdb_ids)).all()
                cluster_ids = [cluster.id for cluster in cluster_results] 

                if cluster_ids:
                    genome_results = Genome.query.filter(Genome.cluster_id.in_(cluster_ids)).all()
                    genome_ids.update([genome.genome_id for genome in genome_results])  


        if country:
            country_results = Geographic.query.whooshee_search(country).all()
            genome_ids.update([g.genome_id for g in country_results])

        if envo_class:
            envo_class_results = EnvironmentOntology.query.whooshee_search(envo_class).all()
            envo_terms = [e.envo_term for e in envo_class_results]
            genome_envo_results = GenomeENVO.query.filter(
                (GenomeENVO.envo_habitat.in_(envo_terms)) | (GenomeENVO.envo_isolation_source.in_(envo_terms))
            ).all()
            genome_ids.update([ge.genome_id for ge in genome_envo_results])

        if envo_annotation:
            envo_annotation_results = EnvironmentOntology.query.whooshee_search(envo_annotation).all()
            envo_terms = [e.envo_term for e in envo_annotation_results]
            genome_envo_results = GenomeENVO.query.filter(
                (GenomeENVO.envo_habitat.in_(envo_terms)) | (GenomeENVO.envo_isolation_source.in_(envo_terms))
            ).all()
            genome_ids.update([ge.genome_id for ge in genome_envo_results])

        query = db.session.query(
            Genome.genome_id,
            Genome.genome_type,
            GTDBTaxon.taxon_path,
            GenomesQuality.quality,
            Geographic.country,
            Geographic.local,
            EnvironmentOntology.envo_class,
            EnvironmentOntology.envo_annotation,
            LiteratureItem.doi,
            NCBI.ncbi_accession,
            Cluster.id.label('cluster_id')
        ).outerjoin(Cluster, Genome.cluster_id == Cluster.id) \
         .outerjoin(GTDBTaxon, Cluster.gtdb_id == GTDBTaxon.id) \
         .outerjoin(GenomesQuality, Genome.genome_id == GenomesQuality.genome_id) \
         .outerjoin(Geographic, Genome.genome_id == Geographic.genome_id) \
         .outerjoin(GenomeENVO, Genome.genome_id == GenomeENVO.genome_id) \
         .outerjoin(EnvironmentOntology, GenomeENVO.envo_habitat == EnvironmentOntology.envo_term) \
         .outerjoin(LiteratureItem, Genome.literature_id == LiteratureItem.id) \
         .outerjoin(NCBI, Genome.genome_id == NCBI.genome_id)

        if genome_ids:
            query = query.filter(Genome.genome_id.in_(list(genome_ids)))

        results = query.all()

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
