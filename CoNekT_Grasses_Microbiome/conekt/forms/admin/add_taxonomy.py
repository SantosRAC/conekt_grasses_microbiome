from flask_wtf import FlaskForm
from wtforms import StringField
from flask_wtf.file import FileField
from wtforms.validators import InputRequired


class AddTaxonomyForm(FlaskForm):
    ncbi_release = StringField('NCBI Release date', [InputRequired()])
    ncbi_taxonomy_nodes_file = FileField('NCBI Taxonomy Nodes File')
    ncbi_taxonomy_names_file = FileField('NCBI Taxonomy Names File')

    silva_release = StringField('SILVA Release', [InputRequired()])
    silva_taxonomy_file = FileField('SILVA Taxonomy File')
    
    gg_release = StringField('GreenGenes Release', [InputRequired()])
    gg_taxonomy_file = FileField('GreenGenes Taxonomy File')