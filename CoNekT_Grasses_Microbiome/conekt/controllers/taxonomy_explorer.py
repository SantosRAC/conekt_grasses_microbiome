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

@taxonomy_explorer.route('/view') # Renderiza o template pra o /taxonomy_explorer/view
def genome_counts_page():
    return render_template('taxonomy_explorer.html')

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
        parent = ''  # Ignora o parent para o nível de domínio
    try:
        # Verifique se o nível taxonômico existe no modelo GTDBTaxon
        if not hasattr(GTDBTaxon, level): # verifica se o módelo GTDBTaxon tem um atributo correspondente ao nível taxonomico fornecido
            current_app.logger.error(f'Level {level} does not exist in GTDBTaxon') # erro se nñao existir no log
            return jsonify({'error': f'Level {level} does not exist in GTDBTaxon'}), 400 # Erro se não existir no JSON

        # Construindo a consulta para todas as categorias
        all_query = (
            db.session.query( #Inicia a consulta no DB
                getattr(GTDBTaxon, level), # Obtém a coluna corresponde ao nível taxonômico no modelo GTDBTaxon
                func.count(func.distinct(Genome.genome_id)).label('count') # Conta o número de genomas (genome_id) e atribui a contagem ao rótulo count
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
    
@taxonomy_explorer.route('/species_genomes/<int:cluster_id>', methods=['GET'])
def show_genomes(cluster_id):
    try:
        genomes = Genome.query.filter_by(cluster_id=cluster_id).all()
        
        # Prepare os dados para serem passados ao template
        genome_data = [{'genome_id': genome.genome_id, 'genome_type': genome.genome_type} for genome in genomes]

        # Passe a lista de dicionários como 'genomes' para o template
        return render_template('species_genomes.html', genomes=genome_data, cluster_id=cluster_id)
    except Exception as e:
        return f"An error occurred: {str(e)}", 500



