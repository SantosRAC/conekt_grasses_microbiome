from flask_wtf import FlaskForm
from flask_wtf.file import FileField



class AddTaxonomyForm(FlaskForm):
    gtdb_taxonomy_data = FileField('GTDB Taxonomy File')