import json
from statistics import mean

from conekt import db

from conekt.models.microbiome.otu_profiles import OTUProfile

# Importing associations with Ontologies
from conekt.models.relationships.sample_po import SamplePOAssociation
from conekt.models.relationships.sample_peco import SamplePECOAssociation
from conekt.models.relationships.sample_envo import SampleENVOAssociation

# Importing other associations considered groups in sample definitions
from conekt.models.relationships.sample_group import SampleGroupAssociation

from utils.entropy import entropy_from_values
from utils.expression import expression_specificity
from utils.tau import tau


class ExpressionSpecificityMethod(db.Model):
    __tablename__ = 'microbiome_specificity_method'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    conditions = db.Column(db.Text)
    data_type = db.Column(db.Enum('condition', 'po_anatomy',
                                  'po_dev_stage', 'peco',
                                  'subpopulation',
                                  name='data_type'))
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'))

    def __repr__(self):
        return str(self.id) + ". " + self.description + ' [' + self.species.name + ']'


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
        #new_method = ExpressionSpecificityMethod()
        #new_method.study_id = study_id
        #new_method.description = description
        
        sample_pos = {}
        sample_pecos = {}
        sample_envos = {}
        sample_groups = {}

        # get profile from the database (ORM free for speed)
        profiles = db.engine.execute(db.select([OTUProfile.__table__.c.id, OTUProfile.__table__.c.profile]).
                                     where(OTUProfile.__table__.c.study_id == study_id)
                                     ).fetchall()
        
        # detect all conditions, assuming all profiles in a study have the same ontologies and groups
        groups_profile = db.engine.execute(db.select([OTUProfile.__table__.c.id, OTUProfile.__table__.c.profile]).
                                     where(OTUProfile.__table__.c.study_id == study_id)
                                     ).first()

        profile_data = json.loads(groups_profile[1])
        
        print(profile_data['data']['sample_id'].values(), '\n\n\n\n\n\n\n')

        exit(1)
            
        #new_method.conditions = json.dumps(tissues)

        #db.session.add(new_method)
        #db.session.commit()

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


class ExpressionSpecificity(db.Model):
    __tablename__ = 'microbiome_specificity'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('otu_profiles.id', ondelete='CASCADE'), index=True)
    condition = db.Column(db.String(255), index=True)
    score = db.Column(db.Float, index=True)
    entropy = db.Column(db.Float, index=True)
    tau = db.Column(db.Float, index=True)
    method_id = db.Column(db.Integer, db.ForeignKey('microbiome_specificity_method.id', ondelete='CASCADE'), index=True)
