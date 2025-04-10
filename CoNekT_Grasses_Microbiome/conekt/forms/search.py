from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import InputRequired


class BasicSearchForm(FlaskForm):
    
    taxonomy = StringField('Taxonomy')
    country = StringField('Country')
    envo_class = SelectField('ENVO Class', choices=[], coerce=str)
    envo_annotation = SelectField('ENVO Annot', choices=[], coerce=str)