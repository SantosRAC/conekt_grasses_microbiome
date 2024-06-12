from copy import deepcopy
from collections import Counter

from flask import url_for
from sqlalchemy.orm import joinedload

from conekt.models.expression.profiles import ExpressionProfile
from conekt.models.sequences import Sequence
from conekt.models.species import Species
from conekt.models.clades import Clade
from utils.color import family_to_shape_and_color, index_to_shape_and_color


class CytoscapeHelper:

    @staticmethod
    def parse_network(network):
        """
        Parses a network generated by the ExpressionNetwork and CoexpressionCluster model, adding basic information
        and exporting the whole thing to a cytoscape.js compatible

        :param network: internal id of the network
        :return: Network fully compatible with Cytoscape.js
        """
        output = {"nodes": [], "edges": []}

        for n in network["nodes"]:
            output["nodes"].append({"data": n})

        for e in network["edges"]:
            output["edges"].append({"data": e})

        # add basic colors and shapes to nodes and url to gene pages

        for n in output["nodes"]:
            if n["data"]["gene_id"] is not None:
                n["data"]["gene_link"] = url_for("sequence.sequence_view", sequence_id=n["data"]["gene_id"])

            if n["data"]["id"] != n["data"]["gene_name"]:
                n["data"]["profile_link"] = url_for("expression_profile.expression_profile_find", probe=n["data"]["id"])

            n["data"]["color"] = "#CCC"
            n["data"]["shape"] = "ellipse"

        for e in output["edges"]:
            e["data"]["color"] = "#888"

        return output

    @staticmethod
    def add_descriptions_nodes(network):
        """
        Adds the description to nodes (if available), the best name to display and alternative names (aka gene tokens)
        to a cytoscape.js network

        :param network: Cytoscape.js compatible network object
        :return: Network with descriptions and tokens added
        """
        completed_network = deepcopy(network)

        sequence_ids = []
        for node in completed_network["nodes"]:
            if "data" in node.keys() and "gene_id" in node["data"].keys():
                sequence_ids.append(node["data"]["gene_id"])

        sequences = Sequence.query.filter(Sequence.id.in_(sequence_ids)).all()

        descriptions = {s.id: s.description for s in sequences}
        best_names = {s.id: s.best_name for s in sequences}
        tokens = {s.id: ", ".join([x.name for x in s.xrefs if x.platform == 'token']) for s in sequences}

        # Set empty tokens to None
        for k, v in tokens.items():
            if v == "":
                tokens[k] = None

        for node in completed_network["nodes"]:
            if "data" in node.keys() and "gene_id" in node["data"].keys():
                if node["data"]["gene_id"] in descriptions.keys():
                    node["data"]["description"] = descriptions[node["data"]["gene_id"]]
                else:
                    node["data"]["description"] = None

                if node["data"]["gene_id"] in best_names.keys():
                    node["data"]["best_name"] = best_names[node["data"]["gene_id"]]
                else:
                    node["data"]["best_name"] = node["data"]["gene_name"]

                if node["data"]["gene_id"] in tokens.keys():
                    node["data"]["tokens"] = tokens[node["data"]["gene_id"]]
                else:
                    node["data"]["tokens"] = None

        return completed_network


    @staticmethod
    def add_species_data_nodes(network):
        """
        Colors nodes in a cytoscape compatible network (dict) based on species

        :param network: dict containing the network
        :return: Cytoscape.js compatible network with depth information for edges added
        """
        colors = {s.id: s.color for s in Species.query.all()}
        colored_network = deepcopy(network)

        for node in colored_network["nodes"]:
            if "data" in node.keys() and "species_id" in node["data"].keys():
                node["data"]["species_color"] = colors[node["data"]["species_id"]]

        return colored_network



    @staticmethod
    def prune_unique_lc(network):
        """
        Remove genes from network that have a unique label (label co-occ.). Requires a Cytoscape.js compatible network
        and will return a purned copy in the same format. Note that label co-occ. need to be present in the
        network *before* applying this function. (e.g. using add_lc_data_nodes in this class)

        :param network: dict containing the network
        :return: Cytoscape.js compatible network with the pruned network
        """

        lc_labels = []
        for node in network["nodes"]:
            if 'lc_label' in node['data'].keys():
                lc_labels.append(node['data']['lc_label'])

        lc_counter = Counter(lc_labels)

        print(lc_counter)

        pruned_network = {'nodes': [], 'edges': []}

        good_nodes = []

        for node in network['nodes']:
            if 'lc_label' in node['data'].keys():
                if lc_counter[node['data']['lc_label']] > 1:
                    good_nodes.append(node['data']['name'])
                    pruned_network['nodes'].append(deepcopy(node))
            else:
                good_nodes.append(node['data']['name'])
                pruned_network['nodes'].append(deepcopy(node))

        for edge in network['edges']:
            if edge['data']['source'] in good_nodes and edge['data']['target'] in good_nodes:
                pruned_network['edges'].append(deepcopy(edge))

        return pruned_network


    @staticmethod
    def get_families(network):
        """
        Extracts gene families from a cytoscape.js compatible network object

        :param network: network to extract families from
        :return: List of all families that occur in the network
        """
        return [f["data"]["family_name"] for f in network["nodes"] if 'data' in f.keys() and
                'family_name' in f["data"].keys() and
                f["data"]["family_name"] is not None]
