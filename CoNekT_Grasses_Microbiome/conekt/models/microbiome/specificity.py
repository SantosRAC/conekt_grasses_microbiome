import json
from statistics import mean

from conekt import db

from conekt.models.microbiome.otu_profiles import OTUProfile
SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

# Importing Ontologies
from conekt.models.ontologies import PlantOntology, PlantExperimentalConditionsOntology, EnvironmentOntology

# Importing associations with Ontologies
from conekt.models.relationships.sample_po import SamplePOAssociation
from conekt.models.relationships.sample_peco import SamplePECOAssociation
from conekt.models.relationships.sample_envo import SampleENVOAssociation

# Importing other associations considered groups in sample definitions
from conekt.models.relationships.sample_group import SampleGroupAssociation

from utils.entropy import entropy_from_values
from utils.expression import expression_specificity
from utils.tau import tau


class MicrobiomeSpecificityMethod(db.Model):
    __tablename__ = 'microbiome_specificity_method'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    conditions = db.Column(db.Text)
    data_type = db.Column(db.Enum('condition', 'po_anatomy',
                                  'po_dev_stage', 'peco',
                                  'envo', 'subpopulation',
                                  name='data_type'))
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'))

    def __init__(self, description, conditions, study_id, data_type='condition'):
        self.description = description
        self.conditions = conditions
        self.study_id = study_id
        self.data_type = data_type

    def __repr__(self):
        return str(self.id) + ". " + self.description + ' [' + self.study_id + ']'

    @staticmethod
    def calculate_specificities(study_id, description, remove_background=False, use_max=True):
        """
        Function calculates specific genes based on the samples ontologies and groups. 
        This also allows conditions to be excluded in case they are unrelated with a specific tissue.

        :param study_id: internal id of the study
        :param description: description for the method to determine the specificity
        :param remove_background: substracts the lowest value to correct for background noise
        :param use_max: uses the maximum of mean values instead of the mean of all values
        :return id of the new method
        """

        # detect all conditions, assuming all profiles in a study have the same ontologies and groups
        groups_profile = OTUProfile.query.with_entities(OTUProfile.id, OTUProfile.profile).\
                                                        filter(OTUProfile.study_id == study_id).first()

        profile_data = json.loads(groups_profile[1])
        
        po_ids = SamplePOAssociation.query.with_entities(SamplePOAssociation.po_id).\
            filter(SamplePOAssociation.sample_id.in_(list(profile_data['data']['sample_id'].values()))).distinct().all()
        peco_ids = SamplePECOAssociation.query.with_entities(SamplePECOAssociation.peco_id).\
            filter(SamplePECOAssociation.sample_id.in_(list(profile_data['data']['sample_id'].values()))).distinct().all()
        envo_ids = SampleENVOAssociation.query.with_entities(SampleENVOAssociation.envo_id).\
            filter(SampleENVOAssociation.sample_id.in_(list(profile_data['data']['sample_id'].values()))).distinct().all()
        
        if po_ids:
            po_ids = [po_id for po_id in po_ids[0]]
        if peco_ids:
            peco_ids = [peco_id for peco_id in peco_ids[0]]
        if envo_ids:
            envo_ids = [envo_id for envo_id in envo_ids[0]]

        sample_groups_dict = {}
        sample_groups_dict['po'] = {}
        sample_groups_dict['peco'] = {}
        sample_groups_dict['envo'] = {}

        sample_groups = SampleGroupAssociation.query.filter(SampleGroupAssociation.sample_id.in_(list(profile_data['data']['sample_id'].values()))).all()

        for sample_group in sample_groups:
            if sample_group.group_type in sample_groups_dict.keys():
                if sample_group.group_name in sample_groups_dict[sample_group.group_type].keys():
                    sample_groups_dict[sample_group.group_type][sample_group.group_name].append(sample_group.sample_id)
                else:
                    sample_groups_dict[sample_group.group_type][sample_group.group_name] = [sample_group.sample_id]
            else:
                sample_groups_dict[sample_group.group_type] = {}
                sample_groups_dict[sample_group.group_type][sample_group.group_name] = [sample_group.sample_id]

        pos = PlantOntology.query.with_entities(PlantOntology.po_class).filter(PlantOntology.id.in_(po_ids)).distinct().all()
        pecos = PlantExperimentalConditionsOntology.query.with_entities(PlantExperimentalConditionsOntology.peco_class).filter(PlantExperimentalConditionsOntology.id.in_(peco_ids)).distinct().all()
        envos = EnvironmentOntology.query.with_entities(EnvironmentOntology.envo_class).filter(EnvironmentOntology.id.in_(envo_ids)).distinct().all()
        
        #TODO: Still need to implment distinctions between PO dev staget and PO anatomy
        if pos and (len(pos) > 1):
            new_method = MicrobiomeSpecificityMethod(description + " - " + "PO",
                                                     str([po for po in pos[0]]),
                                                     study_id, data_type = 'po_anatomy')
            new_method.study_id = study_id
            new_method.description = description + " - " + "PO"
            new_method.data_type = 'po_anatomy'
            new_method.conditions = str([po for po in pos[0]])
            db.session.add(new_method)

            sample_pos = SamplePOAssociation.query.with_entities(SamplePOAssociation.po_id,
                                                             SamplePOAssociation.sample_id).\
            filter(SamplePOAssociation.sample_id.in_(list(profile_data['data']['sample_id'].values()))).distinct().all()
            
            for sample_po in sample_pos:
                if sample_po.po_id in sample_groups_dict['po'].keys():
                    sample_groups_dict['po'][sample_po.po_id].append(sample_po.sample_id)
                else:
                    sample_groups_dict['po'][sample_po.po_id] = [sample_po.sample_id]

        if pecos and (len(pecos) > 1):
            new_method = MicrobiomeSpecificityMethod(description + " - " + "PECO",
                                                     str([peco for peco in pecos[0]]),
                                                     study_id, data_type = 'peco')
            db.session.add(new_method)

            sample_pecos = SamplePECOAssociation.query.with_entities(SamplePECOAssociation.peco_id,
                                                                 SamplePECOAssociation.sample_id).\
            filter(SamplePECOAssociation.sample_id.in_(list(profile_data['data']['sample_id'].values()))).distinct().all()
        
            for sample_peco in sample_pecos:
                if sample_peco.peco_id in sample_groups_dict['peco'].keys():
                    sample_groups_dict['peco'][sample_peco.peco_id].append(sample_peco.sample_id)
                else:
                    sample_groups_dict['peco'][sample_peco.peco_id] = [sample_peco.sample_id]

        if envos and (len(envos) > 1):
            new_method = MicrobiomeSpecificityMethod(description + " - " + "ENVO",
                                                     str([envo for envo in envos[0]]),
                                                     study_id, data_type = 'envo')
            db.session.add(new_method)

            sample_envos = SampleENVOAssociation.query.with_entities(SampleENVOAssociation.envo_id,
                                                                 SampleENVOAssociation.envo_id).\
            filter(SampleENVOAssociation.sample_id.in_(list(profile_data['data']['sample_id'].values()))).distinct().all()

            for sample_envo in sample_envos:
                if sample_envo.envo_id in sample_groups_dict['envo'].keys():
                    sample_groups_dict['envo'][sample_envo.envo_id].append(sample_envo.sample_id)
                else:
                    sample_groups_dict['envo'][sample_envo.envo_id] = [sample_envo.sample_id]

        if 'subpopulation' in sample_groups_dict.keys() and len(sample_groups_dict['subpopulation'].keys()) > 1:
            new_method = MicrobiomeSpecificityMethod(description + " - " + "Subpopulation",
                                                     str([group for group in sample_groups_dict['subpopulation'].keys()]),
                                                     study_id, data_type = 'subpopulation')
            db.session.add(new_method)

        db.session.commit()

        # get all profile from the database for a specified study
        profiles = OTUProfile.query.with_entities(OTUProfile.id, OTUProfile.probe, OTUProfile.profile).\
                                                        filter(OTUProfile.study_id == study_id).all()

        # detect specifities and add to the database
        specificities = []
        new_methods_ids = []

        for profile_id, profile_probe, profile in profiles:
            # prepare profile data for calculation
            profile_data = json.loads(profile)
            profile_means = {}
            for group_type in sample_groups_dict.keys():
                if sample_groups_dict[group_type]:

                    profile_means[group_type] = {}

                    specificity_method = MicrobiomeSpecificityMethod.query.filter(MicrobiomeSpecificityMethod.study_id == study_id,
                                                                                  MicrobiomeSpecificityMethod.data_type == group_type).first()
                    new_methods_ids.append(specificity_method.id)

                    for group_name in sample_groups_dict[group_type].keys():

                        values = []
                        valid_runs = [k for k in profile_data['data']['count'].keys() if profile_data['data']['sample_id'][k] in sample_groups_dict[group_type][group_name]]

                        for k, v in profile_data['data']['count'].items():
                            if k in valid_runs:
                                values = values + [v]
                    
                        profile_means[group_type][group_name] = mean(values)
            
                    # substract minimum value to remove background
                    # experimental code !
                    if remove_background:
                        minimum = min([v for k, v in profile_means[group_type].items()])

                        for k in profile_means.keys():
                            profile_means[k] -= minimum

                    # determine spm score for each condition
                    profile_specificities = []
                    profile_tau = tau([v for v in profile_means[group_type].values()])
                    profile_entropy = entropy_from_values([v for v in profile_means[group_type].values()])

                    for group_name in sample_groups_dict[group_type].keys():
                        score = expression_specificity(group_name, profile_means[group_type])
                        new_specificity = {
                            'profile_id': profile_id,
                            'otu_probe': profile_probe,
                            'condition': group_name,
                            'score': score,
                            'entropy': profile_entropy,
                            'tau': profile_tau,
                            'method_id': specificity_method.id,
                        }
                        profile_specificities.append(new_specificity)
                    
                    # sort conditions and add top one
                    profile_specificities = sorted(profile_specificities, key=lambda x: x['score'], reverse=True)
                    specificities.append(profile_specificities[0])
                    db.session.add(MicrobiomeSpecificity(**profile_specificities[0]))

                    # write specificities to db if there are more than 400 (ORM free for speed)
                    if len(specificities) > 400:
                        db.session.commit()
                        specificities = []

        db.session.commit()
        
        return new_methods_ids


    @staticmethod
    def get_method_specificities(method_id, spm_cutoff=0.5):
        """
        Returns the specific profiles based on the SPM score for a specific method.

        :param method_id: internal id of the method
        :param spm_cutoff: cutoff for the SPM score
        """

        specific_profiles = MicrobiomeSpecificity.query.filter(MicrobiomeSpecificity.method_id == method_id,
                                                               MicrobiomeSpecificity.score >= spm_cutoff).all()

        return specific_profiles   


class MicrobiomeSpecificity(db.Model):
    __tablename__ = 'microbiome_specificity'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('otu_profiles.id', ondelete='CASCADE'), index=True)
    otu_probe = db.Column(db.String(255, collation=SQL_COLLATION), index=True)
    condition = db.Column(db.String(255), index=True)
    score = db.Column(db.Float, index=True)
    entropy = db.Column(db.Float, index=True)
    tau = db.Column(db.Float, index=True)
    method_id = db.Column(db.Integer, db.ForeignKey('microbiome_specificity_method.id', ondelete='CASCADE'), index=True)

    def __init__(self, profile_id, otu_probe, condition, score, entropy, tau, method_id):
        self.profile_id = profile_id
        self.otu_probe = otu_probe
        self.condition = condition
        self.score = score
        self.entropy = entropy
        self.tau = tau
        self.method_id = method_id

    def __repr__(self):
        return str(self.id) + ". " + self.condition + ' (SPM: ' + self.score + ')'  


