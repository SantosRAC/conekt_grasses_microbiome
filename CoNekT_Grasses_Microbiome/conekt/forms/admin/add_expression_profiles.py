from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SelectField
from flask_wtf.file import FileRequired, FileField

from conekt.models.species import Species
from conekt.models.sample import Sample


class AddExpressionProfilesForm(FlaskForm):
    species_id = SelectField('Species', coerce=int)

    normalization_method = SelectField('Normalization method', choices=[('tpm', 'TPM'),
                                                                        ('cpm', 'CPM'),
                                                                        ('tmm', 'TMM'),
                                                                        ('numreads', 'NumReads')])

    matrix_file = FileField()
    annotation_file = FileField()

    def populate_species(self):
        # Get distinct species ids from sample table
        species_ids = []
        for species_id in Sample.query.with_entities(Sample.species_id).distinct().all():
            species_ids.append(species_id[0])
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.filter(Species.id.in_(species_ids)).all()]
