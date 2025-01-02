from flask_wtf import FlaskForm
from wtforms import SelectField, StringField
from flask_wtf.file import FileField
from wtforms.validators import InputRequired

from conekt.models.species import Species
from conekt.models.sample import Sample


class AddOTUAssociationsForm(FlaskForm):
    
    species_id = SelectField('Species', coerce=int, choices=[], validate_choice=False)
    study_id = SelectField('Study', coerce=int, choices=[], validate_choice=False)
    sample_group = SelectField('Sample Group', validate_choice=False)
    description = StringField('Description', [InputRequired()])
    tool = SelectField('Tool', choices=[('sparxcc', 'SparCC'),
                                        ('spiec-easi', 'SPIEC-EASI')])
    method = SelectField('Method', choices=[('spiec-easi-mb', 'Meinshausen-Bühlman (MB)'),
                                        ('spiec-easi-glasso', 'Glasso'),
                                        ('None', 'None')])
    otu_association_file = FileField('OTU Association File')

    def populate_species(self):
        # Get distinct species ids from sample table
        species_ids = [species_id[0] for species_id in Sample.query.with_entities(Sample.species_id).distinct().all()]
        self.species_id.choices = [(0, 'Select Species')] + [(s.id, s.name) for s in Species.query.filter(Species.id.in_(species_ids)).all()]