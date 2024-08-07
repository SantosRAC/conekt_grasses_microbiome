from flask_wtf import FlaskForm
from wtforms import StringField, SelectField

from conekt.models.species import Species


class SearchSpecificProfilesForm(FlaskForm):
    species_id = SelectField('Species')
    study_id = SelectField('Study')
    conditions = SelectField('Condition')
    cutoff = StringField('Cutoff')

    def populate_form(self):
        self.species_id.choices = [(0, "Select species")] + [(s.id, s.name) for s in Species.query.order_by(Species.name)]
        self.study_id.choices = [(0, "Select species first")]
        self.conditions.choices = [(0, "Select study first")]

