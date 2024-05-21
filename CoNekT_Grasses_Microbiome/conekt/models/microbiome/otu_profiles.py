from conekt import db

from sqlalchemy.orm import joinedload, undefer

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class OTUProfileMethod(db.Model):
    __tablename__ = 'otu_profile_methods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255, collation=SQL_COLLATION), unique=True)
    normalization = db.Column(db.Enum('counts', 'cpm', 'tpm', name='Normalization'), default='counts')

    def __init__(self, otu_id, name, normalization):
        self.otu_id = otu_id
        self.name = name
        self.normalization = normalization

    def __repr__(self):
        return str(self.id) + ". " + str(self.name)


class OTUProfile(db.Model):
    __tablename__ = 'otu_profiles'
    id = db.Column(db.Integer, primary_key=True)
    otu_id = db.Column(db.Integer, db.ForeignKey('otus.id', ondelete='CASCADE'), index=True)
    otu_profile_method_id = db.Column(db.Integer, db.ForeignKey('otu_profile_methods.id', ondelete='CASCADE'), index=True)
    profile = db.deferred(db.Column(db.Text))

    def __init__(self, otu_id, otu_profile_method_id, profile):
        self.otu_id = otu_id
        self.otu_profile_method_id = otu_profile_method_id
        self.profile = profile

    def __repr__(self):
        return str(self.id) + ". " + str(self.otu_id) + "(OTU Profile Method ID: " + str(self.otu_profile_method_id) + ")"