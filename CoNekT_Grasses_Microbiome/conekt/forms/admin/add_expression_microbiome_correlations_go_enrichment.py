from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from flask_wtf.file import FileField

from conekt.models.species import Species
from conekt.models.sample import Sample


class AddExpMicrobiomeCorrelationsGOEnrichForm(FlaskForm):
    species_id = SelectField('Species', coerce=int, validate_choice=False)
    study_id = SelectField('Study', coerce=int, validate_choice=False)
    go_enrichment_method = SelectField('GO Enrichment method', choices=[('goatools', 'GOATOOLS'),
                                                             ('test', 'Test (do not use this!)')])
    exp_microbiome_correlation_method = SelectField('Cross-Correlation Method', validate_choice=False)
    go_enrichment_file = FileField()

    def populate_species(self):
        # Get distinct species ids from sample table
        species_ids = []
        for species_id in Sample.query.with_entities(Sample.species_id).distinct().all():
            species_ids.append(species_id[0])
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.filter(Species.id.in_(species_ids)).all()]

