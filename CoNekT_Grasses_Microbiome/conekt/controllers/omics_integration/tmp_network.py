import json
from conekt import db

from flask import Blueprint, url_for, render_template, flash, redirect, Response

from conekt import cache
from conekt.helpers.cytoscape import CytoscapeHelper
from conekt.models.species import Species
from conekt.models.gene_families import GeneFamilyMethod

from utils.benchmark import benchmark

expression_network = Blueprint('expression_network', __name__)


@expression_network.route('/species/<species_id>')
@cache.cached()
def expression_network_species(species_id):
    """
    Overview of all networks in the current database with basic information
    """
    networks = ExpressionNetworkMethod.query.filter_by(species_id=species_id).all()
    species = db.session.get_or_404(Species, species_id)

    return render_template("expression_network.html", networks=networks, species=species)


@expression_network.route('/graph/<node_id>')
@expression_network.route('/graph/<node_id>/<int:family_method_id>')
@cache.cached()
def expression_network_graph(node_id, family_method_id=None):
    """
    Page that displays the network graph for a specific network's probe, the depth indicates how many steps away from
    the query gene the network is retrieved. For performance reasons depths > 1 are not allowed

    :param node_id: id of the network's probe (the query) to visualize
    :param depth: How many steps to include, 0 only the query and the direct neighborhood, 1 a step further, ...
    Currently unused, filtering is done by javascript downstream
    :param family_method_id: family method to use for colors and shapes based on the family
    """
    if family_method_id is None:
        family_method = GeneFamilyMethod.query.first()
        if family_method is not None:
            family_method_id = family_method.id
        else:
            family_method_id = None

    node = ExpressionNetwork.query.get(node_id)
    enable_second_level = node.method.enable_second_level

    depth = 1 if enable_second_level else 0

    return render_template("expression_graph.html", node=node, depth=depth, family_method_id=family_method_id,
                           cutoff=node.method.hrr_cutoff)


@expression_network.route('/json/<node_id>')
@expression_network.route('/json/<node_id>/<int:family_method_id>')
@cache.cached()
def expression_network_json(node_id, family_method_id=None):
    """
    Generates JSON output compatible with cytoscape.js (see planet/static/planet_graph.js for details how to render)

    :param node_id: id of the network's probe (the query) to visualize
    :param family_method_id: Which gene families to use
    """

    node = ExpressionNetwork.query.get(node_id)
    enable_second_level = node.method.enable_second_level
    depth = 1 if enable_second_level else 0

    network = ExpressionNetwork.get_neighborhood(node_id, depth=depth)

    if family_method_id is None:
        family_method = GeneFamilyMethod.query.first()
        if family_method is not None:
            family_method_id = family_method.id
        else:
            family_method_id = None

    network_cytoscape = CytoscapeHelper.parse_network(network)
    network_cytoscape = CytoscapeHelper.add_family_data_nodes(network_cytoscape, family_method_id)
    network_cytoscape = CytoscapeHelper.add_lc_data_nodes(network_cytoscape)
    network_cytoscape = CytoscapeHelper.add_descriptions_nodes(network_cytoscape)

    return Response(json.dumps(network_cytoscape), mimetype='application/json')

