from flask_wtf import FlaskForm

from wtforms import StringField, SelectField, SelectMultipleField, TextAreaField
from flask_wtf.file import FileField
from wtforms.validators import InputRequired

from conekt.models.species import Species
from conekt.models.sample import Sample
from conekt.models.seq_run import SeqRun

class BuildStudyForm(FlaskForm):    
    
    species_id = SelectField('Species', coerce=int, choices=[], validate_choice=False)

    # study Description and type (RNAseq, metataxonomic, both)
    study_name = StringField('Study Name', [InputRequired()])
    study_description = TextAreaField('Study Description')
    study_type = SelectField('Study Type', choices=[('metataxonomics', 'Metataxonomics'),
                                                    ('expression_metataxonomics', 'Both'),])
    
    krona_file = FileField('Krona File')

    def populate_species(self):
        species_ids = []
        for species_id in Sample.query.with_entities(Sample.species_id).distinct().all():
            species_ids.append(species_id[0])
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.filter(Species.id.in_(species_ids)).all()]