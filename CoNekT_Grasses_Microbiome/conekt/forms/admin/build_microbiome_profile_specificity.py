from flask_wtf import FlaskForm
from wtforms.validators import InputRequired
from wtforms import StringField, SelectField

from conekt.models.species import Species

class BuildMicrobiomeSpecificityForm(FlaskForm):
    species_id = SelectField('Species', coerce=int, validate_choice=False)
    study_id = SelectField('Study', coerce=int, validate_choice=False)
    description = StringField('Description', validators=[InputRequired()])

    def populate_species(self):
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.order_by(Species.name)]