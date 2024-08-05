from conekt import db

class StudySampleAssociation(db.Model):
    """Class for StudySampleAssociation model
     
    Class to create a relationship between studies and samples.
    """
    __tablename__ = 'study_samples'
    __table_args__ = (db.UniqueConstraint(
            "study_id", "sample_id",
            name="unique_study_sample"
        ),)

    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'))
    sample_id = db.Column(db.Integer, db.ForeignKey('samples.id', ondelete='CASCADE'))

    def __init__(self, study_id, sample_id):
        self.study_id = study_id
        self.sample_id = sample_id