from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from flask_wtf.file import FileField
from wtforms.validators import InputRequired


class AddASVProfilesForm(FlaskForm):
    
    study_id = SelectField('Study', coerce=int, choices=[], validate_choice=False)

    # Fields for the run annotation
    run_annotation_file = FileField()

    # Fields for the feature table
    feature_table_file = FileField()
    normalization_method = SelectField('Normalization Method', choices=[('tpm', 'TPM'),
                                                                        ('cpm', 'CPM'),
                                                                        ('tmm', 'TMM'),
                                                                        ('numreads', 'NumReads')])