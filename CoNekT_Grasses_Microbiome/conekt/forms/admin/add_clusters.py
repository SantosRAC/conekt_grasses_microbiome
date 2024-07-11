from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed

class AddClustersForm(FlaskForm):
    
    clusters_file = FileField('clusters')
