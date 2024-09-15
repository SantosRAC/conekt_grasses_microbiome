from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, RadioField
from flask_wtf.file import FileField
from wtforms.validators import InputRequired

from conekt.models.microbiome.asvs import AmpliconSequenceVariantMethod
from conekt.models.literature import LiteratureItem


class AddASVClassificationForm(FlaskForm):
    
    literature_id = SelectField('Literature', coerce=int, choices=[], validate_choice=False)
    asv_method_id = SelectField('ASV Method', coerce=int, choices=[], validate_choice=False)

    # Fields for the ASV classification method
    asv_classification_description = StringField('Description', [InputRequired()])
    asv_classification_method_silva = SelectField('ASV classifier (to assign SILVA taxonomy IDs)', choices=[('uclust', 'uclust'),
                                                    ('qiime2_classify-sklearn', 'qiime2_classify-sklearn'),
                                                    ('other', 'Other')])

    classifier_version_silva = StringField('Classifier version (assign SILVA taxonomy IDs)', [InputRequired()])
    release_silva = StringField('Reference Database release', [InputRequired()])

    silva_asv_classification_file = FileField('SILVA ASV Classification File')

    additional_classification = RadioField('Add Additional Classification Databases? (e.g. GTDB)', choices=[('yes', 'Yes'), ('no', 'No')], default='no')

    def populate_literature(self):
        # Get distinct species ids from sample table
        literature_ids = [lit_id[0] for lit_id in AmpliconSequenceVariantMethod.query.with_entities(AmpliconSequenceVariantMethod.literature_id).distinct().all()]
        self.literature_id.choices = [(0, 'Select Literature')] + [(s.id, s.title) for s in LiteratureItem.query.filter(LiteratureItem.id.in_(literature_ids)).all()]