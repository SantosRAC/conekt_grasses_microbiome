import json

from flask import Blueprint, request, render_template, Response
from markupsafe import Markup

from conekt.forms.microbiome.co_occurrence_network import CustomMicrobiomeNetworkForm
from conekt.models.microbiome.otu_associations import MicroAssociation
from conekt.helpers.cytoscape import CytoscapeHelper
from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit

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

        otu_sequences = OperationalTaxonomicUnit.query.filter(OperationalTaxonomicUnit.original_id.in_(otu_probes)).all()

        for s in otu_sequences:
            otu_probes.append(s.original_id)

        # make probe list unique
        otu_probes = list(set(otu_probes))

        microbiome_network = MicroAssociation.create_custom_network(method_id, otu_probes)

        network_cytoscape = CytoscapeHelper.parse_network(microbiome_network)

        return render_template("microbiome/microbiome_graph.html",
                               expression_microbiome_network=expression_microbiome_network,
                               graph_data=Markup(json.dumps(network_cytoscape)))

    else:
        
        return render_template("microbiome/custom_microbiome_network.html", form=form)


@micro_custom_network.route('/sample_group_methods/<study_id>/<sample_group>', methods=['GET', 'POST'])
def sample_group_methods(study_id, sample_group):

    if study_type:
        studies = Study.query.with_entities(Study.id, Study.name).filter_by(species_id=species_id, data_type=study_type).all()

    studyArray = []
    study_ids = []

    for study in studies:
        if study.id in study_ids:
            continue
        else:
            study_ids.append(study.id)
        studyObj = {}
        studyObj['id'] = study.id
        studyObj['name'] = f'{study.name}'
        studyArray.append(studyObj)
    
    return jsonify({'studies': studyArray})