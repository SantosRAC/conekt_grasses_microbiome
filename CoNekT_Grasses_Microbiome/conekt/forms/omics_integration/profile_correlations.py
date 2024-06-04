from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, BooleanField, SelectMultipleField
from wtforms.validators import InputRequired

from conekt.models.species import Species


class StudyExprMicrobiomeCorrelationForm(FlaskForm):
    species_id = SelectField('Species', coerce=int)
    study_id = SelectField('Study', coerce=int)

    def populate_form(self):
        self.species_id.choices = [(s.id, s.name) for s in Species.query.order_by(Species.name)]