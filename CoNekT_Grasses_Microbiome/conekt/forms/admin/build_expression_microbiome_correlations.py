from flask_wtf import FlaskForm
from wtforms.validators import InputRequired
from wtforms import StringField, SelectField

from conekt.models.studies import Study
from conekt.models.species import Species

class BuildExpMicrobiomeCorrelationsForm(FlaskForm):
    species_id = SelectField('Species', coerce=int)
    study_id = SelectField('Study', coerce=int)
    description = StringField('Description', [InputRequired()])
    tool = SelectField('Tool', choices=[('corALS', 'corALS')])
    stat_method = SelectField('Statistical Method', choices=[('pearson', 'pearson'), ('spearman', 'spearman')])
    multiple_test_cor_method = SelectField('P-value correction Method', choices=[('fdr_bh', 'fdr_bh'), ('bonferroni', 'bonferroni')])
    rnaseq_norm = SelectField('RNA-seq Data Normalization', choices=[('numreads', 'numreads'), ('cpm', 'cpm'), ('tpm', 'tpm'), ('tmm', 'tmm')])
    metatax_norm = SelectField('Metataxonomic Data Normalization', choices=[('numreads', 'numreads'), ('cpm', 'cpm'), ('tpm', 'tpm'), ('tmm', 'tmm')])

    def populate_species(self):
        self.species_id.choices = [(s.id, s.name) for s in Species.query.order_by(Species.name)]