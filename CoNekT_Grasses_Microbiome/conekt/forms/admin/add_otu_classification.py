from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SelectField
from flask_wtf.file import FileRequired, FileField
from wtforms.validators import InputRequired

from conekt.models.literature import LiteratureItem
from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnitMethod


class AddOTUClassificationForm(FlaskForm):
    
    literature_id = SelectField('Literature', coerce=int, choices=[], validate_choice=False)
    otu_method_id = SelectField('OTU Method', coerce=int, choices=[], validate_choice=False)

    # Fields for the OTU classification method
    otu_classification_description = StringField('Description', [InputRequired()])
    otu_classification_method_gtdb = SelectField('OTU classifier (to assign GTDB taxonomy IDs)', choices=[('uclust', 'uclust'),
                                                    ('qiime2_classify-sklearn', 'qiime2_classify-sklearn'),
                                                    ('other', 'Other')])

    classifier_version_gtdb = StringField('Classifier version (assign GTDB taxonomy IDs)', [InputRequired()])
    release_gtdb = StringField('Reference Database release', [InputRequired()])

    gtdb_otu_classification_file = FileField('GTDB OTU Classification File')

    exact_path_match = RadioField('Exact Path Match?', choices=[(True, 'Yes'), (False, 'No')], default='no')

    additional_classification = RadioField('Add Additional Classification Databases? (e.g. GreenGenes)', choices=[('yes', 'Yes'), ('no', 'No')], default='no')

    otu_classification_method_gg = SelectField('OTU classifier (to assign GG taxonomy IDs)', choices=[('uclust', 'uclust'),
                                                    ('qiime2_classify-sklearn', 'qiime2_classify-sklearn'),
                                                    ('other', 'Other')])
    classifier_version_gg = StringField('Classifier version (assign GG taxonomy IDs)', [InputRequired()])
    release_gg = StringField('Reference Database release', [InputRequired()])
    
    gg_otu_classification_file = FileField('GG OTU Classification File')

    def populate_literature(self):
        # Get distinct species ids from sample table
        literature_ids = [lit_id[0] for lit_id in OperationalTaxonomicUnitMethod.query.with_entities(OperationalTaxonomicUnitMethod.literature_id).distinct().all()]
        self.literature_id.choices = [(0, 'Select Literature')] + [(s.id, s.title) for s in LiteratureItem.query.filter(LiteratureItem.id.in_(literature_ids)).all()]