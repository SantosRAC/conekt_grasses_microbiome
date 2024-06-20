from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SelectField
from flask_wtf.file import FileRequired, FileField
from wtforms.validators import InputRequired

from conekt.models.species import Species
from conekt.models.sample import Sample


class AddOTUClassificationForm(FlaskForm):
    
    species_id = SelectField('Species', coerce=int, choices=[], validate_choice=False)
    literature_id = SelectField('Literature', coerce=int, choices=[], validate_choice=False)
    otu_method_id = SelectField('OTU Method', coerce=int, choices=[], validate_choice=False)

    # Fields for the OTU classification method
    otu_classification_method_gtdb = SelectField('OTU classifier', choices=[('uclust', 'uclust'),
                                                    ('qiime2_classify-sklearn', 'qiime2_classify-sklearn'),
                                                    ('other', 'Other'),])

    classifier_version_gtdb = StringField('Classifier version', [InputRequired()])
    release_gtdb = StringField('Reference Database release', [InputRequired()])

    gtdb_otu_classification_file = FileField()

    additional_classification = RadioField('Add Additional Classification Databases? (e.g. SILVA)', choices=[('yes', 'Yes'), ('no', 'No')], default='no')

    def populate_species(self):
        # Get distinct species ids from sample table
        species_ids = [species_id[0] for species_id in Sample.query.with_entities(Sample.species_id).distinct().all()]
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.filter(Species.id.in_(species_ids)).all()]