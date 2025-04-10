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

    # Populate ENVO choices
    envo_classes = EnvironmentOntology.query.with_entities(EnvironmentOntology.envo_class).distinct().all()
    envo_annotations = EnvironmentOntology.query.with_entities(EnvironmentOntology.envo_annotation).distinct().all()
    
    form.envo_class.choices = [('', 'Select ENVO Class')] + [(c[0], c[0]) for c in envo_classes if c[0]]
    form.envo_annotation.choices = [('', 'Select ENVO Annotation')] + [(a[0], a[0]) for a in envo_annotations if a[0]]

    if request.method == 'POST':
        taxonomy = request.form.get('taxonomy')
        country = request.form.get('country')
        envo_class = request.form.get('envo_class')
        envo_annotation = request.form.get('envo_annotation')

        # Check if any filter is applied
        if not any([taxonomy, country, envo_class, envo_annotation]):
            return render_template('search.html', results=[], form=form, message="Please apply at least one filter")

        # Initialize sets to store genome IDs for each filter
        taxonomy_genome_ids = set()
        country_genome_ids = set()
        envo_class_genome_ids = set()
        envo_annotation_genome_ids = set()

        # Process taxonomy filter
        if taxonomy:
            # Split the taxonomy term into words and get the first word
            first_word = taxonomy.split()[0].strip()
            
            # Search for exact matches in any taxonomic level
            taxonomy_results = GTDBTaxon.query.filter(
                db.or_(
                    GTDBTaxon.domain == first_word,
                    GTDBTaxon.phylum == first_word,
                    GTDBTaxon.Class == first_word,
                    GTDBTaxon.order == first_word,
                    GTDBTaxon.family == first_word,
                    GTDBTaxon.genus == first_word,
                    GTDBTaxon.species == first_word
                )
            ).all()
            
            gtdb_ids = [taxon.id for taxon in taxonomy_results]

            if gtdb_ids:
                cluster_results = Cluster.query.filter(Cluster.gtdb_id.in_(gtdb_ids)).all()
                cluster_ids = [cluster.id for cluster in cluster_results] 

                if cluster_ids:
                    genome_results = Genome.query.filter(Genome.cluster_id.in_(cluster_ids)).all()
                    taxonomy_genome_ids.update([genome.genome_id for genome in genome_results])

        # Process country filter
        if country:
            country_results = Geographic.query.whooshee_search(country).all()
            country_genome_ids.update([g.genome_id for g in country_results])

        # Process ENVO class filter
        if envo_class:
            envo_class_results = EnvironmentOntology.query.filter(EnvironmentOntology.envo_class == envo_class).all()
            envo_terms = [e.envo_term for e in envo_class_results]
            genome_envo_results = GenomeENVO.query.filter(
                (GenomeENVO.envo_habitat.in_(envo_terms)) | (GenomeENVO.envo_isolation_source.in_(envo_terms))
            ).all()
            envo_class_genome_ids.update([ge.genome_id for ge in genome_envo_results])

        # Process ENVO annotation filter
        if envo_annotation:
            envo_annotation_results = EnvironmentOntology.query.filter(EnvironmentOntology.envo_annotation == envo_annotation).all()
            envo_terms = [e.envo_term for e in envo_annotation_results]
            genome_envo_results = GenomeENVO.query.filter(
                (GenomeENVO.envo_habitat.in_(envo_terms)) | (GenomeENVO.envo_isolation_source.in_(envo_terms))
            ).all()
            envo_annotation_genome_ids.update([ge.genome_id for ge in genome_envo_results])

        # Combine all filters using AND logic
        final_genome_ids = set()
        filter_sets = [
            taxonomy_genome_ids,
            country_genome_ids,
            envo_class_genome_ids,
            envo_annotation_genome_ids
        ]
        
        # Only include sets that have been populated (i.e., their filter was used)
        active_filters = [s for s in filter_sets if s]
        
        if active_filters:
            # Start with the first set
            final_genome_ids = active_filters[0].copy()
            # Intersect with remaining sets
            for s in active_filters[1:]:
                final_genome_ids.intersection_update(s)
        else:
            # If no filters returned any results, return empty
            return render_template('search.html', results=[], form=form, message="No results found for the given filters")

        # Build the query
        query = db.session.query(
            Genome.genome_id,
            Genome.genome_type,
            GTDBTaxon.domain,
            GTDBTaxon.phylum,
            GTDBTaxon.Class,
            GTDBTaxon.order,
            GTDBTaxon.family,
            GTDBTaxon.genus,
            GTDBTaxon.species,
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

        if final_genome_ids:
            query = query.filter(Genome.genome_id.in_(list(final_genome_ids)))
            results = query.all()
        else:
            return render_template('search.html', results=[], form=form, message="No results found for the given filters")

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
