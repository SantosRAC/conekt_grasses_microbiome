# Importações necessárias
from flask import Blueprint, json, jsonify, current_app, render_template, request
from conekt import db
from conekt.models.genome_envo import GenomeENVO
from sqlalchemy import func
from conekt.models.genomes_quality import Genomes_quality
from conekt.models.cluster import Cluster
from conekt.models.genome import Genome
from conekt.models.ontologies import EnvironmentOntology
from conekt.models.literature import LiteratureItem

# Blueprint para o overview
overview = Blueprint('overview', __name__)

@overview.route('/paged_statistics/view')
def paged_statistics():
    total_genomes = db.session.query(func.count(Genome.genome_id)).scalar()
    return render_template('overview.html', total_genomes=total_genomes)

# Rota para retornar os dados do Pie Chart
@overview.route('/paged_statistics/genome_counts_by_habitat')
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
@overview.route('/paged_statistics/genome_counts_by_type')
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
    
@overview.route('/paged_statistics/genome_quality_distribution')
def get_genome_quality_distribution():
    try:
        # Query para obter os dados de qualidade dos genomas
        query = (
            db.session.query(
                func.cast(Genomes_quality.completeness, db.Float).label('completeness'),
                func.cast(Genomes_quality.contamination, db.Float).label('contamination')
            ).all()
        )

        # Organizar os dados para serem usados no gráfico de box plot
        data = {
            'completeness': [float(completeness) for completeness, _ in query],
            'contamination': [float(contamination) for _, contamination in query]
        }

        return jsonify(data)

    except Exception as e:
        current_app.logger.error('Error retrieving genome quality data: %s', str(e))
        return jsonify({'error': 'Error retrieving data'}), 500

@overview.route('/paged_statistics/genome_size_distribution')
def get_genome_size_distribution():
    try:
        # Query para obter os tamanhos dos genomas (em bp) e converter para Mbp com duas casas decimais
        query = (
            db.session.query(
                func.round(func.cast(Genome.length, db.Float) / 1e6, 2).label('size')
            ).all()
        )

        # Organizar os tamanhos em uma lista
        sizes = [float(size) for size, in query]

        # Definir as faixas de tamanhos em Mbp
        bins = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, float('inf')]
        labels = ['< 1 Mbp', '1 - 2 Mbp', '2 - 3 Mbp', '3 - 4 Mbp', '4 - 5 Mbp', 
                  '5 - 6 Mbp', '6 - 7 Mbp', '7 - 8 Mbp', '8 - 9 Mbp', '> 9 Mbp']

        # Contar o número de genomas em cada faixa
        data = {
            label: sum(1 for size in sizes if bins[i] < size <= bins[i+1])
            for i, label in enumerate(labels)
        }

        return jsonify(data)

    except Exception as e:
        current_app.logger.error('Error retrieving genome size data: %s', str(e))
        return jsonify({'error': 'Error retrieving data'}), 500
    
@overview.route('/paged_statistics/genomes_by_year')
def get_genomes_by_year():
    try:
        # Query para obter o número de genomas por ano de publicação
        query = (
            db.session.query(
                LiteratureItem.public_year,
                func.count(Genome.genome_id).label('genome_count')
            )
            .join(Genome, Genome.literature_id == LiteratureItem.id)
            .group_by(LiteratureItem.public_year)
            .order_by(LiteratureItem.public_year)
            .all()
        )

        # Query para contar o número total de publicações
        total_publications = db.session.query(func.count(LiteratureItem.id)).scalar()

        # Organizar os dados
        data = []
        for year, count in query:
            data.append({
                'year': year,
                'genome_count': count
            })

        return jsonify({
            'data': data,
            'total_publications': total_publications
        })

    except Exception as e:
        current_app.logger.error('Error retrieving genomes by year data: %s', str(e))
        return jsonify({'error': 'Error retrieving data'}), 500

@overview.route('/paged_statistics/contigs_distribution')
def get_contigs_distribution():
    try:
        # Query para obter o número de contigs, tamanho do genoma e o tipo de genoma
        query = (
            db.session.query(
                Genome.genome_type,
                Genome.num_contigs,
                Genome.length
            ).all()
        )

        # Organize os dados para o gráfico
        data = {'Isolate': [], 'MAG': [], 'SAG': []}
        for genome_type, num_contigs, length in query:
            if genome_type in data:
                data[genome_type].append({
                    'x': num_contigs,
                    'y': length / 1e6  # Convertendo de bp para Mbp
                })

        return jsonify(data)

    except Exception as e:
        current_app.logger.error('Error retrieving contigs distribution data: %s', str(e))
        return jsonify({'error': 'Error retrieving data'}), 500
