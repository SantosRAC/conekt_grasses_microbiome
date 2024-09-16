from flask import Blueprint, render_template, current_app, redirect, g, flash, url_for

from conekt.models.news import News
from conekt import db
from conekt.models.genome import Genome
from conekt.models.geographic_genomes_information import Geographic
from conekt.models.taxonomy import GTDBTaxon
from conekt.models.cluster import Cluster

main = Blueprint('main', __name__)


@main.route('/')
def screen():
    """
    Shows the main screen
    """

    keyword_examples = current_app.config['KEYWORD_EXAMPLES'] if 'KEYWORD_EXAMPLES' in current_app.config.keys() else None

    news = News.query.order_by(News.posted.desc()).limit(5)

    # Consulta para obter genomas com coordenadas e suas espécies associadas
    genomes_with_coordinates = (db.session.query(Genome, Geographic, GTDBTaxon)
                                .join(Geographic, Geographic.genome_id == Genome.genome_id)
                                .join(Cluster, Cluster.id == Genome.cluster_id)  # Juntar Cluster com Genome
                                .join(GTDBTaxon, GTDBTaxon.id == Cluster.gtdb_id)  # Juntar GTDBTaxon com Cluster
                                .filter(Geographic.lat.isnot(None), Geographic.lon.isnot(None))
                                .all())

    # Preparar dados dos genomas para o template
    genome_data = []
    for genome, geographic, taxon in genomes_with_coordinates:
        genome_data.append({
            'genome_id': genome.genome_id,  # Ainda armazenamos o genome_id se necessário
            'species': taxon.species,       # Adiciona a espécie associada ao genoma
            'lat': float(geographic.lat),
            'lon': float(geographic.lon),
            'local': geographic.local or 'Unknown location'
        })

    return render_template('static_pages/main.html', news=news, keyword_examples=keyword_examples, genome_data=genome_data)


@main.route('/features')
def features():
    """
    Shows overview of features
    """
    return render_template('static_pages/features.html')


@main.route('/about')
def about():
    """
    Shows the about page
    """
    return render_template('static_pages/about.html')


@main.route('/contact')
def contact():
    """
    Shows the about contact
    """
    return render_template('static_pages/contact.html')

@main.route('/data-resources')
def data_resources():
    """
    Shows the data resources page
    """
    return render_template('static_pages/data_resources.html')


@main.route('/disclaimer')
def disclaimer():
    """
    Shows the disclaimer
    """
    return render_template('static_pages/disclaimer.html')


@main.route('/privacy')
def privacy_policy():
    """
    Shows the privacy policy
    """
    return render_template('static_pages/privacy_policy.html')


@main.route('/imprint')
def imprint():
    if g.imprint is not None:
        return redirect(g.imprint)
    else:
        flash("No Imprint URL defined", "warning")
        redirect(url_for("main.main"))
