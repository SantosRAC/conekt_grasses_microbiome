from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SelectField
from flask_wtf.file import FileRequired, FileField
from wtforms.validators import InputRequired

from conekt.models.species import Species
from conekt.models.sample import Sample


class AddOTUSForm(FlaskForm):
    
    species_id = SelectField('Species', coerce=int, choices=[], validate_choice=False)
    literature_doi = StringField('Literature DOI', [InputRequired()])

    # Fields for the OTU method
    amplicon_marker = SelectField('Amplicon Marker', choices=[('16s', '16S'),
                                            ('its', 'ITS')])
    primer_pair = StringField('Primer pair', [InputRequired()])

    otu_method_description = StringField('OTU Method Description', [InputRequired()])
    
    clustering_method = SelectField('Clustering Method', choices=[('de_novo', 'de_novo'),
                                            ('closed_reference', 'closed_reference'),
                                            ('open_reference', 'open_reference')])
    
    clustering_algorithm = SelectField('Clustering Algorithm', choices=[('qiime1', 'qiime1'),
                                            ('vsearch', 'vsearch'), ('usearch', 'usearch'),
                                            ('swarm', 'swarm'), ('dada2', 'dada2'),
                                            ('deblur', 'deblur')])
    clustering_threshold = StringField('Clustering Threshold', [InputRequired()])
    clustering_reference_database = StringField('Clustering Reference Database', [InputRequired()])
    clustering_reference_db_release = StringField('Reference Database release', [InputRequired()])
    
    otus_file = FileField()

    # Fields for the run annotation
    run_annotation_file = FileField()

    # Fields for the feature table
    feature_table_file = FileField()
    
    # Fields for the ASV classification method
    otu_classification_description = StringField('OTU Classification Method Description', [InputRequired()])
    otu_classification_method = SelectField('OTU classifier', choices=[('uclust', 'uclust'),
                                                    ('other', 'Other'),])

    classifier_version = StringField('Classifier version', [InputRequired()])
    ref_db_release = StringField('Reference Database version (currently only SILVA and GreenGenes are accepted)', [InputRequired()])

    otu_classification_file = FileField()

    def populate_species(self):
        # Get distinct species ids from sample table
        species_ids = [species_id[0] for species_id in Sample.query.with_entities(Sample.species_id).distinct().all()]
        self.species_id.choices = [(s.id, s.name) for s in Species.query.filter(Species.id.in_(species_ids)).all()]