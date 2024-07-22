from flask_wtf import FlaskForm
from wtforms.validators import InputRequired
from wtforms import StringField, SelectField

from conekt.models.species import Species

class BuildExpMicrobiomeCorrelationsForm(FlaskForm):
    species_id = SelectField('Species', coerce=int, validate_choice=False)
    study_id = SelectField('Study', coerce=int, validate_choice=False)
    description = StringField('Description', [InputRequired()])
    tool = SelectField('Tool', choices=[('corALS', 'corALS')], validate_choice=False)
    stat_method = SelectField('Statistical Method', choices=[('pearson', 'pearson'), ('spearman', 'spearman')],
                              validate_choice=False)
    multiple_test_cor_method = SelectField('P-value correction Method', choices=[('bonferroni', 'bonferroni')],
                                           validate_choice=False) # only bonferroni is available (fdr_bh requires Tbytes of memory using CorALS full correlation)
    rnaseq_norm = SelectField('RNA-seq Data Normalization', choices=[('numreads', 'numreads'), ('cpm', 'cpm'), ('tpm', 'tpm'), ('tmm', 'tmm')],
                              validate_choice=False)
    metatax_norm = SelectField('Metataxonomic Data Normalization', choices=[('numreads', 'numreads'), ('cpm', 'cpm'), ('tpm', 'tpm'), ('tmm', 'tmm')],
                               validate_choice=False)
    correlation_cutoff = StringField('Correlation Cutoff', [InputRequired()])
    corrected_pvalue_cutoff = StringField('Corrected P-value Cutoff', [InputRequired()])

    def populate_species(self):
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.order_by(Species.name)]