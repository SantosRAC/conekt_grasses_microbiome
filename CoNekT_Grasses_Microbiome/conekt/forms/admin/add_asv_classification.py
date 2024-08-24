from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, RadioField
from flask_wtf.file import FileField
from wtforms.validators import InputRequired


class AddASVClassificationForm(FlaskForm):
    
    literature_id = SelectField('Literature', coerce=int, choices=[], validate_choice=False)
    asv_method_id = SelectField('ASV Method', coerce=int, choices=[], validate_choice=False)

    # Fields for the ASV classification method
    asv_classification_description = StringField('Description', [InputRequired()])
    asv_classification_method_gtdb = SelectField('ASV classifier (to assign GTDB taxonomy IDs)', choices=[('uclust', 'uclust'),
                                                    ('qiime2_classify-sklearn', 'qiime2_classify-sklearn'),
                                                    ('other', 'Other')])

    classifier_version_gtdb = StringField('Classifier version (assign GTDB taxonomy IDs)', [InputRequired()])
    release_gtdb = StringField('Reference Database release', [InputRequired()])

    gtdb_asv_classification_file = FileField('GTDB ASV Classification File')

    exact_path_match = RadioField('Exact Path Match?', choices=[(True, 'Yes'), (False, 'No')], default='no')

    additional_classification = RadioField('Add Additional Classification Databases? (e.g. SILVA)', choices=[('yes', 'Yes'), ('no', 'No')], default='no')