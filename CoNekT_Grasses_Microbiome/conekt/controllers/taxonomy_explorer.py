# Importações necessárias
from flask import Blueprint, json, jsonify, current_app, render_template, request
from conekt import db
from conekt.models.genome_envo import GenomeENVO
from sqlalchemy import func
from conekt.models.taxonomy import GTDBTaxon
from conekt.models.cluster import Cluster
from conekt.models.genome import Genome
from conekt.models.ontologies import EnvironmentOntology
from conekt.models.geographic_genomes_information import Geographic
from conekt.models.ncbi_information import NCBI

# Blueprint para o overview
taxonomy_explorer = Blueprint('taxonomy_explorer', __name__)

@taxonomy_explorer.route('/view') # Renderiza o template pra o /taxonomy_explorer/view
def genome_counts_page():
    return render_template('taxonomy_explorer.html')

@taxonomy_explorer.route('/search')
def search_taxonomy():
    query = request.args.get('query', '').strip().lower()

    if not query:
        return jsonify([])

    try:
        levels = ['domain', 'phylum', 'Class', 'order', 'family', 'genus', 'species']
        search_results = []

        for level in levels:
            search_query = (
                db.session.query(
                    getattr(GTDBTaxon, level),
                    func.count(func.distinct(Genome.genome_id)).label('count')
                )
                .join(Cluster, Cluster.gtdb_id == GTDBTaxon.id)
                .join(Genome, Genome.cluster_id == Cluster.id)
                .filter(func.lower(getattr(GTDBTaxon, level)).like(f"%{query}%"))
                .group_by(getattr(GTDBTaxon, level))
                .all()
            )
            search_results.extend([{'name': result[0], 'count': result[1], 'level': level} for result in search_query])

            # Se a busca encontrou resultados, interrompe a busca nos níveis subsequentes
            if search_results:
                break

        return jsonify(search_results)

    except Exception as e:
        current_app.logger.error(f'Error searching taxonomy: {str(e)}')
        return jsonify({'error': 'Error searching taxonomy'}), 500

# Função para determinar o nível pai
def get_parent_level(current_level):
    levels = ['domain', 'phylum', 'Class', 'order', 'family', 'genus', 'species']
    current_index = levels.index(current_level)
    return levels[current_index - 1] if current_index > 0 else None #determina o nível atual e volta um index para determinar o nível pai. No caso de ser o index 0 (dominio) retorna None

# Rota para retornar os dados do Donut chart
@taxonomy_explorer.route('/genome_counts/<level>')
def get_genome_counts(level):
    parent = request.args.get('parent', '')
    
    if level == 'domain':
        parent = ''  # Ignore parent for domain level
    
    try:
        # Check if the taxonomic level exists in the GTDBTaxon model
        if not hasattr(GTDBTaxon, level):  # Verify if GTDBTaxon has an attribute corresponding to the level
            current_app.logger.error(f'Level {level} does not exist in GTDBTaxon')
            return jsonify({'error': f'Level {level} does not exist in GTDBTaxon'}), 400

        # Build the query for all categories
        all_query = (
            db.session.query(
                getattr(GTDBTaxon, level),  # Get the column corresponding to the taxonomic level
                func.count(func.distinct(Genome.genome_id)).label('count')
            )
            .join(Cluster, Cluster.gtdb_id == GTDBTaxon.id)
            .join(Genome, Genome.cluster_id == Cluster.id)
            .group_by(getattr(GTDBTaxon, level))
        )

        if parent:
            parent_level = get_parent_level(level)
            if parent_level is None:
                current_app.logger.error(f'No parent level found for {level}')
                return jsonify({'error': 'Invalid parent level'}), 400

            # Apply the parent filter to limit the results to the correct taxonomic group
            all_query = all_query.filter(getattr(GTDBTaxon, parent_level) == parent)

        all_data = all_query.all()

        # Check if no data is found
        if not all_data:
            current_app.logger.error(f'No data found for level {level} and parent {parent}')
            return jsonify({'error': 'No data found for this level and parent'}), 404

        # Modify for species level: include cluster_id and filter by genus
        if level == 'species':
            # Rebuild the query to include cluster_id for species and apply the parent filter (genus in this case)
            all_query = (
                db.session.query(
                    getattr(GTDBTaxon, level),
                    func.count(func.distinct(Genome.genome_id)).label('count'),
                    Cluster.id.label('cluster_id')  # Capture the cluster_id
                )
                .join(Cluster, Cluster.gtdb_id == GTDBTaxon.id)
                .join(Genome, Genome.cluster_id == Cluster.id)
                .filter(getattr(GTDBTaxon, get_parent_level('species')) == parent)  # Filter by parent genus
                .group_by(getattr(GTDBTaxon, level), Cluster.id)
            )

            # Re-run the query with cluster_id
            all_data = all_query.all()

            # Top 10 query with cluster_id
            top_10_query = all_query.order_by(func.count(func.distinct(Genome.genome_id)).desc()).limit(10).all()

            # Return species data including cluster_id
            data = {
                'all': [{'name': name, 'count': count, 'cluster_id': cluster_id} for name, count, cluster_id in all_data],
                'top_10': [{'name': name, 'count': count, 'cluster_id': cluster_id} for name, count, cluster_id in top_10_query]
            }

        else:
            # Query for top 10 categories (without cluster_id for other levels)
            top_10_query = all_query.order_by(func.count(func.distinct(Genome.genome_id)).desc()).limit(10).all()

            # Return all data for other levels
            data = {
                'all': [{'name': name, 'count': count} for name, count in all_data],
                'top_10': [{'name': name, 'count': count} for name, count in top_10_query]
            }

        return jsonify(data)
    
    except Exception as e:
        current_app.logger.error(f'Error retrieving data for level {level}: {str(e)}')
        return jsonify({'error': 'Error retrieving data'}), 500


@taxonomy_explorer.route('/species_genomes/<int:cluster_id>', methods=['GET'])
def show_genomes(cluster_id):
    try:
        # Fetch the species name 
        species_name = (
            db.session.query(GTDBTaxon.species)
            .join(Cluster, Cluster.gtdb_id == GTDBTaxon.id)
            .filter(Cluster.id == cluster_id)
            .first()
        )

        # Query to get genome data along with geographic and ontology information through GenomeENVO
        genomes = (
            db.session.query(
                Genome.genome_id,
                Genome.genome_type,
                Geographic.country,
                Geographic.local,
                Geographic.lat,  # Include latitude
                Geographic.lon,  # Include longitude
                EnvironmentOntology.envo_class,
                EnvironmentOntology.envo_annotation,
                NCBI.ncbi_accession
            )
            .outerjoin(Geographic, Geographic.genome_id == Genome.genome_id)  # Outer join for geographic data
            .outerjoin(GenomeENVO, GenomeENVO.genome_id == Genome.genome_id)  # Join GenomeENVO to link to ontologies
            .outerjoin(EnvironmentOntology, EnvironmentOntology.envo_term == GenomeENVO.envo_habitat)  # Join for envo_class and envo_annotation
            .outerjoin(NCBI, NCBI.genome_id == Genome.genome_id)
            .filter(Genome.cluster_id == cluster_id)  # Filter by the cluster_id for the selected species
            .all()
        )
        
        # Prepare the data to be passed to the front-end
        genome_data = [
            {
                'genome_id': genome.genome_id,
                'genome_type': genome.genome_type,
                'country': genome.country,
                'local': genome.local,
                'lat': float(genome.lat) if genome.lat else None,  # Pass latitude as float
                'lon': float(genome.lon) if genome.lon else None,  # Pass longitude as float
                'envo_class': genome.envo_class,
                'envo_annotation': genome.envo_annotation,
                'ncbi_accession': genome.ncbi_accession
            }
            for genome in genomes
        ]

        # Pass the species name and genome data to the template
        return render_template('species_genomes.html', genomes=genome_data, species_name=species_name[0], cluster_id=cluster_id)
    except Exception as e:
        current_app.logger.error(f"An error occurred: {str(e)}")
        return f"An error occurred: {str(e)}", 500


    




