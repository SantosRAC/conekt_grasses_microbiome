# Importações necessárias
from flask import Blueprint, jsonify, current_app
from conekt import db
from conekt.models.genome_envo import GenomeENVO
from sqlalchemy import func

# Blueprint para o overview
overview = Blueprint('overview', __name__)

# Rota para retornar os dados do Pie Chart
@overview.route('/genome_counts_by_habitat')
def get_genome_count_by_habitat():
    try:
        query = (
            db.session.query(
                GenomeENVO.envo_habitat,
                func.count(GenomeENVO.genome_id).label('genome_count')
            )
            .group_by(GenomeENVO.envo_habitat)
            .all()
        )

        data = [{'envo_habitat': habitat, 'genome_count': count} for habitat, count in query]

        return jsonify(data)
    except Exception as e:
        current_app.logger.error('Erro ao recuperar dados do Pie Chart: %s', str(e))
        return jsonify({'error': 'Erro ao recuperar dados'}), 500
    