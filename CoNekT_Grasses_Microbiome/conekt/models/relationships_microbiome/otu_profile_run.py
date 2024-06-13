from conekt import db


class OTUProfileRunAssociation(db.Model):
    __tablename__ = 'otu_profile_runs'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    otu_profile_id = db.Column(db.Integer, db.ForeignKey('otu_profiles.id', ondelete='CASCADE'), nullable=False)
    run_id = db.Column(db.Integer, db.ForeignKey('sequencing_runs.id', ondelete='CASCADE'), nullable=False)

    def __init__(self, otu_profile_id, run_id):
        self.otu_profile_id = otu_profile_id
        self.run_id = run_id