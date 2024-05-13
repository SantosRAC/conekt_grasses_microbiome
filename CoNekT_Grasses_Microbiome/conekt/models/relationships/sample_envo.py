from conekt import db

class SampleENVOAssociation(db.Model):
    __tablename__ = 'sample_envo'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.Integer, db.ForeignKey('samples.id', ondelete='CASCADE'))
    envo_id = db.Column(db.Integer, db.ForeignKey('environment_ontology.id', ondelete='CASCADE'))
    species_id = db.Column(db.Integer, db.ForeignKey('species.id', ondelete='CASCADE'))

    species = db.relationship('Species', backref=db.backref('envo_associations',
                                                              lazy='dynamic',
                                                              passive_deletes=True), lazy='joined')

    def __init__(self, sample_id, envo_id):
        self.sample_id = sample_id
        self.envo_id = envo_id