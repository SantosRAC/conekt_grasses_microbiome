from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SelectField
from flask_wtf.file import FileRequired, FileField
from wtforms.validators import InputRequired

from conekt.models.species import Species
from conekt.models.sample import Sample


class AddASVSForm(FlaskForm):
    
    species_id = SelectField('Species', coerce=int, choices=[], validate_choice=False)
    literature_doi = StringField('Literature DOI', [InputRequired()])

    # Fields for the ASV method
    asv_method_description = StringField('ASV Method Description', [InputRequired()])
    amplicon_marker = SelectField('Amplicon Marker', choices=[('16s', '16S'),
                                            ('its', 'ITS')])
    primer_pair = StringField('Primer pair', [InputRequired()])
    asv_source_method = SelectField('ASV Source', choices=[('dada2', 'DADA2'),
                                            ('deblur', 'Deblur')])
    
    asvs_file = FileField()

    # Fields for the run annotation
    run_annotation_file = FileField()

    # Fields for the feature table
    feature_table_file = FileField()
    
    # Fields for the ASV classification method
    asv_classification_description = StringField('ASV Classification Method Description', [InputRequired()])
    asv_classification_method = SelectField('ASV classifier',
                                            choices=[('classify-sklearn', 'classify-sklearn'),
                                                    ('other', 'Other'),])

    classifier_version = StringField('Classifier version', [InputRequired()])
    ref_db_release = StringField('Reference Database version (currently only SILVA is accepted)', [InputRequired()])

    asv_classification_file = FileField()

    def populate_species(self):
        # Get distinct species ids from sample table
        species_ids = [species_id[0] for species_id in Sample.query.with_entities(Sample.species_id).distinct().all()]
        print("species_ids: ", species_ids, "\n\n\n\n\n\n\n\n")
        self.species_id.choices = [(s.id, s.name) for s in Species.query.filter(Species.id.in_(species_ids)).all()]