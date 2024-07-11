from flask_wtf import FlaskForm
from flask_wtf.file import FileField

class AddGenomesForm(FlaskForm):
    
    genomes_file = FileField('genomes')
