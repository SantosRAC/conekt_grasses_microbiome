from flask_wtf import FlaskForm
from wtforms import StringField
from flask_wtf.file import FileField
from wtforms.validators import InputRequired


class AddTaxonomyForm(FlaskForm):
    silva_release = StringField('SILVA Release', [InputRequired()])
    silva_taxonomy_file = FileField('SILVA Taxonomy File')
    
    gg_release = StringField('GreenGenes Release', [InputRequired()])
    gg_taxonomy_file = FileField('GreenGenes Taxonomy File')

    gtdb_release = StringField('GTDB Release', [InputRequired()])
    gtdb_taxonomy_file = FileField('GTDB Taxonomy File')