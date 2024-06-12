from flask_wtf import FlaskForm
from wtforms import SelectField
from flask_wtf.file import FileField

from conekt.models.species import Species


class AddSamplesForm(FlaskForm):
    species_id = SelectField('Species', coerce=int, choices=[], validate_choice=False)

    samples_file = FileField()

    def populate_species(self):
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.order_by(Species.name)]
