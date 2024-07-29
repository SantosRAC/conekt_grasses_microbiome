import json
from statistics import mean

from conekt import db

from conekt.models.microbiome.otu_profiles import OTUProfile

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

        sample_groups = SampleGroupAssociation.query.filter(SampleGroupAssociation.sample_id.in_(list(profile_data['data']['sample_id'].values()))).all()
        
        sample_groups_dict = {}

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
        
        final_list = []
        
        if pos:
            final_list = final_list+[po for po in pos[0]]
        if pecos:
            final_list = final_list+[peco for peco in pecos[0]]
        if envos:
            final_list = final_list+[envo for envo in envos[0]]
        
        # get all profile from the database for a specified study
        profiles = OTUProfile.query.with_entities(OTUProfile.id, OTUProfile.profile).\
                                                        filter(OTUProfile.study_id == study_id).all()

        if pos and (len(pos) > 1):
            new_method = MicrobiomeSpecificityMethod()
            new_method.study_id = study_id
            new_method.description = description + " - " + "PO"
            new_method.data_type = 'po_anatomy'
            new_method.conditions = str([po for po in pos[0]])
            db.session.add(new_method)
        if pecos and (len(pecos) > 1):
            new_method = MicrobiomeSpecificityMethod()
            new_method.study_id = study_id
            new_method.description = description + " - " + "PECO"
            new_method.data_type = 'peco'
            new_method.conditions = str([peco for peco in pecos[0]])
            db.session.add(new_method)
        if envos and (len(envos) > 1):
            new_method = MicrobiomeSpecificityMethod()
            new_method.study_id = study_id
            new_method.data_type = 'envo'
            new_method.description = description + " - " + "ENVO"
            new_method.conditions = str([envo for envo in envos[0]])
            db.session.add(new_method)
        #if 'subpopulation' in sample_groups_dict.keys() and len(sample_groups_dict['subpopulation'].keys()) > 1:
        new_method = MicrobiomeSpecificityMethod()
        new_method.study_id = study_id
        new_method.data_type = 'subpopulation'
        new_method.description = description + " - " + "Subpopulation"
        new_method.conditions = str([group for group in sample_groups_dict['subpopulation'].keys()])
        db.session.add(new_method)

        db.session.commit()

        exit(1)

        # detect specifities and add to the database
        specificities = []

        for profile_id, profile in profiles:
            # prepare profile data for calculation
            profile_data = json.loads(profile)
            profile_means = {}
            for t in tissues:
                values = []
                valid_conditions = [k for k in profile_data['data']['tpm'].keys() if k in condition_to_tissue and condition_to_tissue[k] == t]

                for k, v in profile_data['data']['tpm'].items():
                    if k in valid_conditions:
                        if profile_data['data']['po_anatomy_class'][k] == t:
                            values = values + [v]
                
                profile_means[t] = mean(values)
            
            # substract minimum value to remove background
            # experimental code !
            if remove_background:
                minimum = min([v for k, v in profile_means.items()])

                for k in profile_means.keys():
                    profile_means[k] -= minimum

            # determine spm score for each condition
            profile_specificities = []
            profile_tau = tau([v for v in profile_data['data']['tpm'].values()])
            profile_entropy = entropy_from_values([v for v in profile_data['data']['tpm'].values()])

            for t in tissues:
                score = expression_specificity(t, profile_means)
                new_specificity = {
                    'profile_id': profile_id,
                    'condition': t,
                    'score': score,
                    'entropy': profile_entropy,
                    'tau': profile_tau,
                    'method_id': new_method.id,
                }

                profile_specificities.append(new_specificity)

            # sort conditions and add top one
            profile_specificities = sorted(profile_specificities, key=lambda x: x['score'], reverse=True)

            specificities.append(profile_specificities[0])

            # write specificities to db if there are more than 400 (ORM free for speed)
            if len(specificities) > 400:
                db.engine.execute(ExpressionSpecificity.__table__.insert(), specificities)
                specificities = []

        # write remaining specificities to the db
        db.engine.execute(ExpressionSpecificity.__table__.insert(), specificities)
        return new_method.id


class MicrobiomeSpecificity(db.Model):
    __tablename__ = 'microbiome_specificity'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('otu_profiles.id', ondelete='CASCADE'), index=True)
    condition = db.Column(db.String(255), index=True)
    score = db.Column(db.Float, index=True)
    entropy = db.Column(db.Float, index=True)
    tau = db.Column(db.Float, index=True)
    method_id = db.Column(db.Integer, db.ForeignKey('microbiome_specificity_method.id', ondelete='CASCADE'), index=True)
