from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from flask_wtf.file import FileField
from wtforms.validators import InputRequired

from conekt.models.species import Species
from conekt.models.sample import Sample


class AddExpMicrobiomeCorrelationsForm(FlaskForm):
    species_id = SelectField('Species', coerce=int, validate_choice=False)
    study_id = SelectField('Study', coerce=int, validate_choice=False)
    description = StringField('Description', [InputRequired()])
    stat_method = SelectField('Statistical method', choices=[('sparxcc', 'SparXCC'),
                                                             ('test', 'Test (do not use this!)')])
    sample_group = SelectField('Sample Group', validate_choice=False)
    matrix_file = FileField()

    def populate_species(self):
        # Get distinct species ids from sample table
        species_ids = []
        for species_id in Sample.query.with_entities(Sample.species_id).distinct().all():
            species_ids.append(species_id[0])
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.filter(Species.id.in_(species_ids)).all()]