from flask_wtf import FlaskForm

from wtforms import StringField, SelectField, SelectMultipleField, TextAreaField
from flask_wtf.file import FileField
from wtforms.validators import InputRequired

from conekt.models.species import Species
from conekt.models.sample import Sample
from conekt.models.seq_run import SeqRun

class BuildStudyForm(FlaskForm):    
    
    study_category = SelectField('Study Type', choices=[('ocean', 'Ocean Microbiomes'),
                                                    ('agriculture', 'Agriculture Microbiomes'),
                                                    ('human', 'Human Microbiomes')])

    # study Description and type (RNAseq, metataxonomic, both)
    study_name = StringField('Study Name', [InputRequired()])
    study_description = TextAreaField('Study Description')
    
    krona_file = FileField('Krona File')