from flask_wtf import FlaskForm
from flask_wtf.file import FileField


class AddOntologyDataForm(FlaskForm):
    po = FileField('PO')
    peco = FileField('PECO')
    envo = FileField('ENVO')