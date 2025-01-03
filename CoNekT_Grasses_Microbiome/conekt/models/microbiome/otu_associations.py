from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

from conekt.models.studies import Study
from conekt.models.microbiome.otu_profiles import OTUProfile
from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit


class MicroAssociationMethod(db.Model):
    __tablename__ = 'otu_association_methods'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    sample_group = db.Column(db.String(255, collation=SQL_COLLATION), default='whole study')
    tool_name = db.Column(db.Enum('sparcc', 'spiec-easi', name='Tool'), default='spiec-easi')
    method = db.Column(db.Enum('spiec-easi-mb', 'spiec-easi-glasso', name='Method'), default=None)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'), index=True)

    def __init__(self, description, sample_group, tool_name, method, study_id):
        self.description = description
        self.sample_group = sample_group
        self.tool_name = tool_name
        self.method = method
        self.study_id = study_id
    
    def __repr__(self):
        return str(self.id)


class MicroAssociation(db.Model):
    __tablename__ = 'otu_associations'
    id = db.Column(db.Integer, primary_key=True)
    association_value = db.Column(db.Float)
    metatax_profile1_id = db.Column(db.Integer, db.ForeignKey('otu_profiles.id', ondelete='CASCADE'), index=True)
    metatax_profile2_id = db.Column(db.Integer, db.ForeignKey('otu_profiles.id', ondelete='CASCADE'), index=True)
    otu_probe1 = db.Column(db.String(255, collation=SQL_COLLATION), index=True)
    otu_probe2 = db.Column(db.String(255, collation=SQL_COLLATION), index=True)
    otu_association_method_id = db.Column(db.Integer, db.ForeignKey('otu_association_methods.id', ondelete='CASCADE'), index=True)

    def __init__(self, otu_association_method_id,
                 association_value, metatax_profile1_id, metatax_profile2_id,
                 otu_probe1, otu_probe2):
        self.otu_association_method_id = otu_association_method_id
        self.association_value = association_value
        self.metatax_profile1_id = metatax_profile1_id
        self.metatax_profile2_id = metatax_profile2_id
        self.otu_probe1 = otu_probe1
        self.otu_probe2 = otu_probe2
    
    def __repr__(self):
        return str(self.id)

    @staticmethod
    def add_otu_associations(study_id, sample_group, description,
                             tool_name, method, associations_file):
        """
        Add associations between OTUs
        Currently, only Spiec-Easi and SparCC are implemented
        
        :param study_id: internal id of the study
        :param sample_group: sample group to calculate the correlation
        :param description: description of the correlation method
        :param tool_name: name of the tool used to compute associations
        :param method: method used to compute associations
        :param associations_file: path to the associations file (edge list)
        """

        new_association_method = MicroAssociationMethod(description=description, tool_name=tool_name, method=method,
                                                            study_id=study_id, sample_group=sample_group)

        db.session.add(new_association_method)
        db.session.commit()

        # Get study
        study = Study.query.get(study_id)
        
        with open(associations_file, 'r') as fin:

            new_association_pairs = 0
            
            _ = fin.readline()

            for line in fin:
                otu1_name, otu2_name, association_value = line.rstrip().split()

                otu1_p = OTUProfile.query.filter_by(probe=str(otu1_name),
                    species_id=study.species_id).first()
                otu2_p = OTUProfile.query.filter_by(probe=str(otu2_name),
                    species_id=study.species_id).first()

                new_association_pair = MicroAssociation(otu_probe1=otu1_name,
                                                        otu_probe2=otu2_name,
                                                        metatax_profile1_id=otu1_p.id,
                                                        metatax_profile2_id=otu2_p.id,
                                                        otu_association_method_id=new_association_method.id,
                                                        association_value=association_value)

                db.session.add(new_association_pair)
                new_association_pairs += 1

                if new_association_pairs % 400 == 0:
                    db.session.commit()

            db.session.commit()

        return new_association_pairs
    
    @staticmethod
    def create_custom_network(association_method_id, otu_probes):
        """
        Return a network dict for a certain set of probes, for a certain study, group and method

        :param association_method_id: association method to extract information from
        :param otu_probes: list of probe/otu sequence names
        :return: network dict
        """
        otu_nodes = []
        edges = []

        otu_sequences = OperationalTaxonomicUnit.query.filter(OperationalTaxonomicUnit.original_id.in_(otu_probes)).all()

        valid_otu_nodes = []

        for s in otu_sequences:
            otu_node = {"id": str(s.id) + "_otu",
                    "name": s.original_id,
                    "node_type": "otu",
                    "depth": 0}

            otu_nodes.append(otu_node)
            valid_otu_nodes.append(s.original_id)
        
        for s in otu_sequences:
            microbiome_associations = MicroAssociation.query.filter((MicroAssociation.otu_probe1 == s.original_id) | (MicroAssociation.otu_probe2 == s.original_id),
                MicroAssociation.otu_association_method_id == association_method_id
            ).all()
            for cor_result in microbiome_associations:

                # Create nodes if they do not exist
                otu1_profile = OTUProfile.query.filter_by(id=cor_result.metatax_profile1_id).first()
                otu2_profile = OTUProfile.query.filter_by(id=cor_result.metatax_profile2_id).first()
                if otu1_profile.probe not in valid_otu_nodes:
                    otu_node = {"id": str(otu1_profile.otu_id) + "_otu",
                    "name": str(otu1_profile.probe),
                    "node_type": "otu",
                    "depth": 0}
                    otu_nodes.append(otu_node)
                    valid_otu_nodes.append(str(otu1_profile.probe))
                if otu2_profile.probe not in valid_otu_nodes:
                    otu_node = {"id": str(otu2_profile.otu_id) + "_otu",
                    "name": str(otu2_profile.probe),
                    "node_type": "otu",
                    "depth": 0}
                    otu_nodes.append(otu_node)
                    valid_otu_nodes.append(str(otu2_profile.probe))

                has_edge = [ed for ed in edges if (ed["source"]==str(otu1_profile.otu_id) + "_otu" and ed["target"]==str(otu2_profile.otu_id) + "_otu") or\
                    (ed["source"]==str(otu2_profile.otu_id) + "_otu" and ed["target"]==str(otu1_profile.otu_id) + "_otu")]
                if not has_edge:
                    edges.append({"source": str(otu1_profile.otu_id) + "_otu",
                                "target": str(otu2_profile.otu_id) + "_otu",
                                "source_name": otu1_profile.probe,
                                "target_name": otu2_profile.probe,
                                "depth": 0,
                                "link_cc": cor_result.association_value,
                                "edge_type": "association",
                                "correlation_method": cor_result.otu_association_method_id})

        return {"nodes": otu_nodes, "edges": edges}
