from flask_wtf import FlaskForm
from wtforms.validators import InputRequired
from wtforms import StringField, SelectField

from conekt.models.studies import Study


class BuildExpMicrobiomeCorrelationsForm(FlaskForm):
    study_id = SelectField('Study', coerce=int)
    description = StringField('Description', [InputRequired()])

    def populate_studies(self):
        self.study_id.choices = [(s.id, str(s))
                                   for s in Study.query.all()]
