# Importações necessárias
from flask import Blueprint, json, jsonify, current_app, render_template
from conekt import db
from conekt.models.genome_envo import GenomeENVO
from sqlalchemy import func
from conekt.models.taxonomy import GTDBTaxon
from conekt.models.cluster import Cluster
from conekt.models.genome import Genome
from conekt.models.ontologies import EnvironmentOntology

# Blueprint para o overview
overview = Blueprint('overview', __name__)

@overview.route('/view')
def genome_counts_page():
    return render_template('overview.html')

# Rota para retornar os dados do Bar Chart
@overview.route('/genome_counts_by_taxonomic_level')
def get_genome_counts_by_taxonomic_level():
    try:
        levels = ['domain', 'phylum', 'Class', 'order', 'family', 'genus', 'species']
        data = {}

        # Query para obter a contagem total de registros para cada nível taxonômico
        for level in levels:
            # Verifica se o atributo existe no modelo GTDBTaxon
            if not hasattr(GTDBTaxon, level):
                current_app.logger.warning('Level %s does not exist in GTDBTaxon', level)
                continue

            query = (
                db.session.query(
                    getattr(GTDBTaxon, level),
                    func.count(func.distinct(getattr(GTDBTaxon, level)))
                )
                .join(Cluster, Cluster.gtdb_id == GTDBTaxon.id)
                .join(Genome, Genome.cluster_id == Cluster.id)
                .group_by(getattr(GTDBTaxon, level))
                .all()
            )

            # Calcula o total de registros únicos por nível taxonômico
            total_count = sum(count for _, count in query)

            # Armazena o total no dicionário de dados
            data[level] = total_count

            # Log de depuração para cada nível taxonômico
            current_app.logger.debug('Level: %s, Total: %s', level, total_count)

        # Tenta serializar os dados para JSON e registra as informações
        json_data = json.dumps(data)
        current_app.logger.info('Dados JSON válidos: %s', json_data)

        return jsonify(data)
    
    except Exception as e:
        current_app.logger.error('Erro ao recuperar dados por nível taxonômico: %s', str(e))
        return jsonify({'error': 'Erro ao recuperar dados'}), 500

# Rota para retornar os dados do Pie Chart
@overview.route('/genome_counts_by_habitat')
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
@overview.route('/genome_counts_by_type')
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

   
    

