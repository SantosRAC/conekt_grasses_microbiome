import json

from flask import Blueprint, request, render_template, Response
from markupsafe import Markup

from conekt.forms.omics_integration.expression_microbiome_network import CustomExpMicrobiomeNetworkForm
from conekt.models.expression_microbiome.expression_microbiome_correlation import ExpMicroCorrelation
from conekt.helpers.cytoscape import CytoscapeHelper
from conekt.models.sequences import Sequence

custom_network = Blueprint('custom_network', __name__)


@custom_network.route('/', methods=['GET', 'POST'])
def expression_microbiome_correlation():
    """
    Custom network tool, accepts a species, a study, a method and a list of probes and plots the network
    """
    form = CustomExpMicrobiomeNetworkForm(request.form)
    form.populate_species()

    if request.method == 'POST':
        terms = request.form.get('probes').split()
        method_id = request.form.get('method_id')

        probes = terms

        # also do search by gene ID
        sequences = Sequence.query.filter(Sequence.name.in_(terms)).filter_by(type='protein_coding').all()

        for s in sequences:
            probes.append(s.name)

        # make probe list unique
        probes = list(set(probes))

        expression_microbiome_network = ExpMicroCorrelation.create_custom_network(method_id, probes)

        network_cytoscape = CytoscapeHelper.parse_network(expression_microbiome_network)

        return render_template("omics_integration/expression_microbiome_graph.html",
                               expression_microbiome_network=expression_microbiome_network,
                               graph_data=Markup(json.dumps(network_cytoscape)))

    else:
        
        return render_template("omics_integration/custom_expression_microbiome_network.html", form=form)

