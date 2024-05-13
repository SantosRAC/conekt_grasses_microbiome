from conekt import db

import json

from conekt.models.microbiome.asvs import AmpliconSequenceVariant
from conekt.models.seq_run import SeqRun
from conekt.models.relationships_microbiome.asv_profile_run import ASVProfileRunAssociation

from sqlalchemy.orm import joinedload, undefer

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class ASVProfile(db.Model):
    __tablename__ = 'asv_profiles'
    id = db.Column(db.Integer, primary_key=True)
    asv_id = db.Column(db.Integer, db.ForeignKey('asvs.id', ondelete='CASCADE'), index=True)
    asv_method_id = db.Column(db.Integer, db.ForeignKey('asv_methods.id', ondelete='CASCADE'), index=True)
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

    @staticmethod
    def get_profiles(probes, asv_profiles_ids, limit=1000):
        """
        Gets the data for a set of probes (including the full profiles), a limit can be provided to avoid overly
        long queries

        :param species_id: internal id of the species
        :param probes: probe names to fetch
        :param limit: maximum number of probes to get
        :return: List of ExpressionProfile objects including the full profiles
        """
        profiles = ASVProfile.query.\
            options(undefer(ASVProfile.profile)).\
            filter(ASVProfile.asv_id.in_(probes), ASVProfile.id.in_(asv_profiles_ids)).\
            options(joinedload(ASVProfile.asv).load_only(AmpliconSequenceVariant.original_id)).\
            limit(limit).all()

        return profiles

    @staticmethod
    def add_asv_profiles_from_table(feature_table, species_id, asv_method_id):
        """
        Function to generate an ASV profile

        :param feature_table: path to the feature table
        :param asv_method_id: internal id of the method used to generate the ASV
        :param species_id: internal id of the species
        """

        added_asv_profiles = 0

        # build conversion table for asvs
        asvs = AmpliconSequenceVariant.query.filter_by(method_id=asv_method_id).all()
        asv_seq_dict = {}  # key = sequence name uppercase, value internal id
        for a in asvs:
            asv_seq_dict[a.original_id.upper()] = a.id

        with open(feature_table, 'r') as fin:

            # read header
            _, *colnames = fin.readline().rstrip().split()

            # build conversion table for asvs
            runs = SeqRun.query.filter(SeqRun.accession_number.in_(colnames)).\
                                all()
            seq_run_dict = {}  # key = sequence name uppercase, value internal id
            for r in runs:
                seq_run_dict[r.accession_number.upper()] = r.id

            # read each line and build ASV profile
            new_asv_profiles = []

            for line in fin:
                asv_name, *values = line.rstrip().split()

                profile = {'count': {},
                           'run': {},
                           'run_id': {}}

                asv = AmpliconSequenceVariant.query.filter_by(original_id=asv_name).first()

                for c, v in zip(colnames, values):
                    profile['count'][c] = int(v)
                    profile['run_id'][c] = seq_run_dict[c.upper()]
                    profile['run'][c] = c.upper()

                new_profile = ASVProfile(**{"asv_id": asv.id,
                                "asv_method_id": asv_method_id,
                                "profile": json.dumps({"data": profile})
                                })
                
                new_asv_profiles.append(new_profile)
                added_asv_profiles+=1
                db.session.add(new_profile)
                db.session.commit()

                for run in runs:
                    new_asv_profile_run = {"asv_profile_id": new_profile.id,
                                           "run_id": run.id}
                    db.session.add(ASVProfileRunAssociation(**new_asv_profile_run))
                
                db.session.commit()

        return added_asv_profiles


"""class PhylotypeProfile(db.Model):
    __tablename__ = 'phylotype_profiles'
    id = db.Column(db.Integer, primary_key=True)
    phylotype_id = db.Column(db.Integer, db.ForeignKey('phylotypes.id', ondelete='CASCADE'), index=True)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'), index=True)
    profile = db.deferred(db.Column(db.Text))

    def __init__(self, asv_id, study_id, profile):
        self.asv_id = asv_id
        self.study_id = study_id
        self.profile = profile

    def __repr__(self):
        return str(self.id) + ". " + self.asv_id + "(Study ID: " + self.study_id + ")"
    
    @staticmethod
    def add_phylotype_profile(species_id):
        TODO: implement this function
        """