from conekt import db


class StudyRunAssociation(db.Model):
    """Class for StudyRunAssociation model

    Class to create a relationship between studies and runs.
    Runs will be associated with a study depending on the samples used in the run
    and the study type (if expression + microbiome, runs from both types in a
    sample will be associated with that study).
    """
    __tablename__ = 'study_runs'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'), nullable=False)
    run_id = db.Column(db.Integer, db.ForeignKey('sequencing_runs.id', ondelete='CASCADE'), nullable=False)
    data_type = db.Column(db.Enum('rnaseq', 'metataxonomics', name='data_type'), nullable=False)

    def __init__(self, study_id, run_id, data_type):
        self.study_id = study_id
        self.run_id = run_id
        self.data_type = data_type