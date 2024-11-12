from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired


class BasicSearchForm(FlaskForm):
    
    taxonomy = StringField('Taxonomy')
    country = StringField('Country')
    envo_class = StringField('ENVO Class')
    envo_annotation = StringField('ENVO Annot')