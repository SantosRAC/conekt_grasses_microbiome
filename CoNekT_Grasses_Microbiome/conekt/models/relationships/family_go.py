from conekt import db


class FamilyGOAssociation(db.Model):
    __tablename__ = 'family_go'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    gene_family_id = db.Column(db.Integer, db.ForeignKey('gene_families.id', ondelete='CASCADE'))
    go_id = db.Column(db.Integer, db.ForeignKey('go.id', ondelete='CASCADE'))

    go_term = db.relationship('GO', backref=db.backref('family_associations',
                              lazy='dynamic', passive_deletes=True), lazy='joined')
