from conekt import db


class ASVProfileRunAssociation(db.Model):
    __tablename__ = 'asv_profile_runs'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    asv_profile_id = db.Column(db.Integer, db.ForeignKey('asv_profiles.id', ondelete='CASCADE'), nullable=False)
    run_id = db.Column(db.Integer, db.ForeignKey('sequencing_runs.id', ondelete='CASCADE'), nullable=False)

    def __init__(self, asv_profile_id, run_id):
        self.asv_profile_id = asv_profile_id
        self.run_id = run_id