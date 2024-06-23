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
            if n["data"]["id"] is not None and n["data"]["node_type"] == "gene":
                n["data"]["gene_link"] = url_for("sequence.sequence_view", sequence_id=n["data"]["id"])
                n["data"]["color"] = "#26837c"
            
            if n["data"]["id"] is not None and n["data"]["node_type"] == "otu":
                n["data"]["otu_link"] = url_for("otu.otu_view", otu_id=n["data"]["id"])
                n["data"]["color"] = "#852e2e"

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