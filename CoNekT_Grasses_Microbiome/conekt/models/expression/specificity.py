import json
from statistics import mean

from conekt import db
from conekt.models.expression.profiles import ExpressionProfile
from utils.entropy import entropy_from_values
from utils.expression import expression_specificity
from utils.tau import tau


# TODO: add decorator for Solr
class ExpressionSpecificityMethod(db.Model):
    __tablename__ = 'expression_specificity_method'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    conditions = db.Column(db.Text)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id', ondelete='CASCADE'), index=True)

    specificities = db.relationship('ExpressionSpecificity',
                                    backref='method',
                                    lazy='dynamic',
                                    cascade="all, delete-orphan",
                                    passive_deletes=True)

    condition_tissue = db.relationship('ConditionTissue', backref='expression_specificity_method', lazy='joined',
                                       cascade="all, delete-orphan",
                                       passive_deletes=True, uselist=False)

    menu_order = db.Column(db.Integer)

    def __repr__(self):
        return str(self.id) + ". " + self.description + ' [' + self.species.name + ']'


    @staticmethod
    def calculate_specificities(species_id, description, remove_background=False, use_max=True):
        """
        Function calculates condition and tissue specific genes based on the expression conditions. 
        This also allows conditions to be excluded in case they are unrelated with a specific tissue.

        :param species_id: internal species ID
        :param description: description for the method to determine the specificity
        :param condition_to_tissue: dict to connect a condition to a tissue
        :param order: preferred order of the conditions, will match tissues to it
        :param remove_background: substracts the lowest value to correct for background noise
        :param use_max: uses the maximum of mean values instead of the mean of all values
        :return id of the new method
        """
        new_method = ExpressionSpecificityMethod()
        new_method.species_id = species_id
        new_method.description = description
        new_method.menu_order = 0
        
        condition_to_tissue = {}

        # get profile from the database (ORM free for speed)
        profiles = db.session.execute(db.select(ExpressionProfile.id, ExpressionProfile.profile).
                                      where(ExpressionProfile.species_id == species_id)
                                     ).all()

        # detect all conditions
        for profile_id, profile in profiles:
            profile_data = json.loads(profile)
            for condition, po in profile_data['data']['PO_class'].items():
                condition_to_tissue[condition] = po

        tissues = list(sorted(set(profile_data['data']['PO_class'].values())))

        new_method.conditions = json.dumps(tissues)

        db.session.add(new_method)
        db.session.commit()

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
                        if profile_data['data']['PO_class'][k] == t:
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

            specificities.append(ExpressionSpecificity(**profile_specificities[0]))

            # write specificities to db if there are more than 400 (ORM free for speed)
            if len(specificities) > 400:
                db.session.add_all(specificities)
                db.session.commit()
                specificities = []

        # write remaining specificities to the db
        db.session.add_all(specificities)
        db.session.commit()
        return new_method.id


class ExpressionSpecificity(db.Model):
    __tablename__ = 'expression_specificity'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('expression_profiles.id', ondelete='CASCADE'), index=True)
    condition = db.Column(db.String(255), index=True)
    score = db.Column(db.Float, index=True)
    entropy = db.Column(db.Float, index=True)
    tau = db.Column(db.Float, index=True)
    method_id = db.Column(db.Integer, db.ForeignKey('expression_specificity_method.id', ondelete='CASCADE'), index=True)
