from flask_wtf import FlaskForm
from wtforms import StringField
from flask_wtf.file import FileField, FileRequired
from wtforms.validators import InputRequired


class AddTaxonomyForm(FlaskForm):
    ncbi_release = StringField('NCBI Release', [InputRequired()])
    ncbi_taxonomy_file = FileField('NCBI Taxonomy File')

    silva_release = StringField('SILVA Release', [InputRequired()])
    silva_taxonomy_file = FileField('SILVA Taxonomy File')