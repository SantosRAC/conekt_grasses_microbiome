from flask_wtf import FlaskForm
from wtforms import SelectField

from conekt.models.species import Species

class BuildStudyPCAsForm(FlaskForm):
    species_id = SelectField('Species', coerce=int, validate_choice=False)
    study_id = SelectField('Study', coerce=int, validate_choice=False)
    rnaseq_norm = SelectField('RNA-seq Data Normalization', choices=[('numreads', 'numreads'), ('cpm', 'cpm'), ('tpm', 'tpm'), ('tmm', 'tmm')],
                              validate_choice=False)
    metatax_norm = SelectField('Metataxonomic Data Normalization', choices=[('numreads', 'numreads'), ('cpm', 'cpm'), ('tpm', 'tpm'), ('tmm', 'tmm')],
                               validate_choice=False)

    def populate_species(self):
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.order_by(Species.name)]