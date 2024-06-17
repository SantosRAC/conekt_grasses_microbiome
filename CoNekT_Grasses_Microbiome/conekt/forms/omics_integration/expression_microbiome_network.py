from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField
from wtforms.validators import InputRequired

from conekt.models.species import Species


class CustomExpMicrobiomeNetworkForm(FlaskForm):
    species_id = SelectField('Species', coerce=int)
    study_id = SelectField('Study', coerce=int)
    method_id = SelectField('Method', coerce=int)
    probes = TextAreaField('probes', [InputRequired()])

    def populate_species(self):
        self.species_id.choices = [(0, 'Select Species first')] + [(s.id, s.name) for s in Species.query.order_by(Species.name)]


    