# Importações necessárias
from flask import Blueprint, json, jsonify, current_app, render_template, request
from conekt import db
from conekt.models.genome_envo import GenomeENVO
from sqlalchemy import func
from conekt.models.taxonomy import GTDBTaxon
from conekt.models.cluster import Cluster
from conekt.models.genome import Genome
from conekt.models.ontologies import EnvironmentOntology

# Blueprint para o overview
taxonomy_explorer = Blueprint('taxonomy_explorer', __name__)

@taxonomy_explorer.route('/view')
def genome_counts_page():
    return render_template('taxonomy_explorer.html')

# Função para determinar o nível pai
def get_parent_level(current_level):
    levels = ['domain', 'phylum', 'Class', 'order', 'family', 'genus', 'species']
    current_index = levels.index(current_level)
    return levels[current_index - 1] if current_index > 0 else None

# Rota para retornar os dados do Bar Chart
@taxonomy_explorer.route('/genome_counts/<level>')
def get_genome_counts(level):
    parent = request.args.get('parent', '')
    
    if level == 'domain':
        parent = ''  # Ignora o parent para o nível de domínio
    try:
        # Verifique se o nível taxonômico existe no modelo GTDBTaxon
        if not hasattr(GTDBTaxon, level):
            current_app.logger.error(f'Level {level} does not exist in GTDBTaxon')
            return jsonify({'error': f'Level {level} does not exist in GTDBTaxon'}), 400

        # Construindo a consulta para todas as categorias
        all_query = (
            db.session.query(
                getattr(GTDBTaxon, level),
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
            all_query = all_query.filter(getattr(GTDBTaxon, parent_level) == parent)

        all_data = all_query.all()

        # Verifica se não há dados
        if not all_data:
            current_app.logger.error(f'No data found for level {level} and parent {parent}')
            return jsonify({'error': 'No data found for this level and parent'}), 404

        # Consulta para as 10 principais categorias
        top_10_query = all_query.order_by(func.count(func.distinct(Genome.genome_id)).desc()).limit(10).all()

        # Retornando todos os dados e as 10 principais categorias
        data = {
            'all': [{'name': name, 'count': count} for name, count in all_data],
            'top_10': [{'name': name, 'count': count} for name, count in top_10_query]
        }

        return jsonify(data)
    
    except Exception as e:
        current_app.logger.error(f'Erro ao recuperar dados para o nível {level}: {str(e)}')
        return jsonify({'error': 'Erro ao recuperar dados'}), 500


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

    

# Rota para retornar os dados do Pie Chart
@taxonomy_explorer.route('/genome_counts_by_habitat')
def get_genome_count_by_habitat():
    try:
        # Query para contar o número de genomas por classe ENVO
        query = (
            db.session.query(
                EnvironmentOntology.envo_class,
                func.count(GenomeENVO.genome_id).label('genome_count')
            )
            .join(GenomeENVO, GenomeENVO.envo_habitat == EnvironmentOntology.envo_term)
            .group_by(EnvironmentOntology.envo_class)
            .all()
        )

        # Total de genomas para calcular proporções
        total_genomes = db.session.query(func.count(GenomeENVO.genome_id)).scalar()

        # Lista para armazenar os dados no formato {envo_class: nome_da_classe, genome_proportion: proporção}
        data = []
        for env_class, count in query:
            proportion = (count / total_genomes) * 100 if total_genomes > 0 else 0.0
            data.append({
                'envo_class': env_class,
                'genome_proportion': proportion
            })

        return jsonify(data)

    except Exception as e:
        current_app.logger.error('Error retrieving genome counts by habitat: %s', str(e))
        return jsonify({'error': 'Error retrieving data'}), 500
    
# Rota para retornar os dados do Pie Chart
@taxonomy_explorer.route('/genome_counts_by_type')
def get_genome_count_by_type():
    try:
        # Obter o número total de genomas
        total_genomes = db.session.query(func.count(Genome.genome_id)).scalar()

        # Query para contar os genomas por tipo
        query = (
            db.session.query(
                Genome.genome_type,
                func.count(Genome.genome_id).label('count')
            )
            .group_by(Genome.genome_type)
            .all()
        )

        # Calcular a proporção de cada tipo de genoma
        data = [{'genome_type': genome_type, 'proportion': (count / total_genomes) * 100} for genome_type, count in query]

        return jsonify(data)
    except Exception as e:
        current_app.logger.error('Error retrieving genome types data: %s', str(e))
        return jsonify({'error': 'Error retrieving data'}), 500