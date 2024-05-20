from conekt import db

from sqlalchemy.orm import joinedload, undefer

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class OTUProfileMethod(db.Model):
    __tablename__ = 'otu_profile_methods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255, collation=SQL_COLLATION), unique=True)
    

    __table_args__ = (
        db.Index("idx_asv_profiles_asv_id_asv_method_id", asv_id, asv_method_id, unique=True),
        db.UniqueConstraint(asv_id, asv_method_id, name='u_asv_profiles_asv_id_asv_method_id'),
    )

    def __init__(self, asv_id, asv_method_id, profile):
        self.asv_id = asv_id
        self.asv_method_id = asv_method_id
        self.profile = profile

    def __repr__(self):
        return str(self.id) + ". " + str(self.asv_id) + "(ASV Creation Method ID: " + str(self.asv_method_id) + ")"



class OTUProfile(db.Model):
    __tablename__ = 'otu_profiles'
    id = db.Column(db.Integer, primary_key=True)
    otu_id = db.Column(db.Integer, db.ForeignKey('otus.id', ondelete='CASCADE'), index=True)
    otu_profile_method_id = db.Column(db.Integer, db.ForeignKey('otu_profile_methods.id', ondelete='CASCADE'), index=True)
    profile = db.deferred(db.Column(db.Text))

    __table_args__ = (
        db.Index("idx_asv_profiles_asv_id_asv_method_id", asv_id, asv_method_id, unique=True),
        db.UniqueConstraint(asv_id, asv_method_id, name='u_asv_profiles_asv_id_asv_method_id'),
    )

    def __init__(self, asv_id, asv_method_id, profile):
        self.asv_id = asv_id
        self.asv_method_id = asv_method_id
        self.profile = profile

    def __repr__(self):
        return str(self.id) + ". " + str(self.asv_id) + "(ASV Creation Method ID: " + str(self.asv_method_id) + ")"