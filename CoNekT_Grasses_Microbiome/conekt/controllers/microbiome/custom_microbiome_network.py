import json

from flask import Blueprint, request, render_template, Response, jsonify
from markupsafe import Markup

from conekt.forms.microbiome.co_occurrence_network import CustomMicrobiomeNetworkForm
from conekt.models.microbiome.otu_associations import MicroAssociation
from conekt.helpers.cytoscape import CytoscapeHelper

from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit
from conekt.models.microbiome.otu_associations import MicroAssociationMethod

micro_custom_network = Blueprint('micro_custom_network', __name__)


@micro_custom_network.route('/', methods=['GET', 'POST'])
def cooccurrence_network():
    """
    Custom network tool, accepts a species, a study, a method and a list of OTU probes the network
    """
    form = CustomMicrobiomeNetworkForm(request.form)
    form.populate_species()

    if request.method == 'POST':
        otu_terms = request.form.get('otu_probes').split()
        sample_group = request.form.get('sample_group')
        method_id = request.form.get('method_id')

        otu_probes = otu_terms

        microbiome_network = MicroAssociation.create_custom_network(method_id, otu_probes)

        network_cytoscape = CytoscapeHelper.parse_network(microbiome_network)

        return render_template("microbiome/microbiome_graph.html",
                               microbiome_network=microbiome_network,
                               graph_data=Markup(json.dumps(network_cytoscape)))

    else:
        
        return render_template("microbiome/custom_microbiome_network.html", form=form)


@micro_custom_network.route('/sample_group_methods/<study_id>/<sample_group_selection>', methods=['GET', 'POST'])
def sample_group_methods(study_id, sample_group_selection):

    otu_association_methods = MicroAssociationMethod.query.filter_by(study_id=study_id, sample_group=sample_group_selection).all()

    methodsArray = []

    for method in otu_association_methods:
        methodObj = {}
        methodObj['id'] = method.id
        methodObj['description'] = f'{method.description}'
        methodObj['tool_name'] = f'{method.tool_name}'
        methodObj['method'] = f'{method.method}'
        methodsArray.append(methodObj)
    
    return jsonify({'association_methods': methodsArray})