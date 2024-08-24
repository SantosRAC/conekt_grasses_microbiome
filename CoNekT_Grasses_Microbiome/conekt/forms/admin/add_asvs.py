from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from flask_wtf.file import FileField
from wtforms.validators import InputRequired


class AddASVSForm(FlaskForm):
    
    literature_doi = StringField('Literature DOI', [InputRequired()])

    # Fields for the ASV method
    asv_method_description = StringField('ASV Method Description', [InputRequired()])
    amplicon_marker = SelectField('Amplicon Marker', choices=[('16s', '16S'),
                                            ('its', 'ITS')])
    primer_pair = StringField('Primer pair', [InputRequired()])
    asv_source_method = SelectField('ASV Source', choices=[('dada2', 'DADA2'),
                                            ('deblur', 'Deblur')])
    
    asvs_file = FileField()