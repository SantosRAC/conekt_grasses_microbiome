from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from flask_wtf.file import FileField
from wtforms.validators import InputRequired

from conekt.models.species import Species
from conekt.models.sample import Sample


class AddOTUProfilesForm(FlaskForm):
    
    species_id = SelectField('Species', coerce=int, choices=[], validate_choice=False)
    study_id = SelectField('Study', coerce=int, choices=[], validate_choice=False)

    # Fields for the run annotation
    run_annotation_file = FileField()

    # Fields for the feature table
    feature_table_file = FileField()
    normalization_method = SelectField('Normalization Method', choices=[('tpm', 'TPM'),
                                                                        ('cpm', 'CPM'),
                                                                        ('tmm', 'TMM'),
                                                                        ('numreads', 'NumReads')])

    def populate_species(self):
        # Get distinct species ids from sample table
        species_ids = [species_id[0] for species_id in Sample.query.with_entities(Sample.species_id).distinct().all()]
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.filter(Species.id.in_(species_ids)).all()]