from flask_wtf import FlaskForm
from wtforms import StringField, SelectField

from conekt.models.species import Species


class SearchSpecificProfilesForm(FlaskForm):
    species = SelectField('Species')
    study = SelectField('Study')
    conditions = SelectField('Condition')
    cutoff = StringField('Cutoff')

    def populate_form(self):
        self.species.choices = [(0, "Select species")] + [(s.id, s.name) for s in Species.query.order_by(Species.name)]
        self.study.choices = [(0, "Select species first")]
        self.conditions.choices = [(0, "Select study first")]

