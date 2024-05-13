from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField
from wtforms.validators import InputRequired

from conekt.models.species import Species
from conekt.models.studies import Study


class ProfileComparisonForm(FlaskForm):
    species_id = SelectField('Species', coerce=int)
    study_id = SelectField('Study', coerce=int)
    probes = TextAreaField('probes', [InputRequired()])

    def populate_species(self):
        # Populate species for which microbiome (or RNAseq ~ Microbiome) studies are available
        species_ids = []
        for species_id in Study.query.with_entities(Study.species_id).distinct().all():
            species_ids.append(species_id[0])
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.filter(Species.id.in_(species_ids)).all()]