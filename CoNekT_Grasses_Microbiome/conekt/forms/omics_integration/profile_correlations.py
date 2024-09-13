from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField
from wtforms.validators import InputRequired

from conekt.models.species import Species

class SearchCorrelatedProfilesStudyGroupsForm(FlaskForm):
    species_id = SelectField('Species', coerce=int)
    study_id = SelectField('Study', coerce=int)
    tool_name = SelectField('Tool', coerce=int)
    correlation_cutoff_study_groups = TextAreaField('Correlation Coefficient Cutoff')

    def populate_form(self):
        self.species_id.choices = [(0, 'Select Species first')] + [(s.id, s.name) for s in Species.query.order_by(Species.name)]


class SearchCorrelatedProfilesGroupForm(FlaskForm):
    species_id = SelectField('Species', coerce=int)
    study_id = SelectField('Study', coerce=int)
    method_id = SelectField('Method', coerce=int)
    sample_group = SelectField('Sample Group', coerce=int)
    correlation_cutoff_groups = TextAreaField('Correlation Coefficient Cutoff')

    def populate_form(self):
        self.species_id.choices = [(0, 'Select Species first')] + [(s.id, s.name) for s in Species.query.order_by(Species.name)]


class SearchCorrelatedProfilesTwoStudiesForm(FlaskForm):
    species_id = SelectField('Species', coerce=int)
    study1_id = SelectField('First Study', coerce=int)
    study2_id = SelectField('Second Study', coerce=int)
    sample_group = SelectField('Sample Group', coerce=int)
    method_id = SelectField('Method', coerce=int)
    correlation_cutoff = TextAreaField('Correlation Coefficient Cutoff')

    def populate_form(self):
        self.species_id.choices = [(0, 'Select Species first')] + [(s.id, s.name) for s in Species.query.order_by(Species.name)]