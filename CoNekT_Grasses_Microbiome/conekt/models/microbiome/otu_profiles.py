from conekt import db

from sqlalchemy.orm import joinedload, undefer

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

import json
from statistics import mean

from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit
from conekt.models.seq_run import SeqRun
from conekt.models.relationships_microbiome.otu_profile_run import OTUProfileRunAssociation


class OTUProfile(db.Model):
    __tablename__ = 'otu_profiles'
    id = db.Column(db.Integer, primary_key=True)
    normalization_method = db.Column(db.Enum('numreads', 'cpm', 'tpm', 'tmm'), default='numreads')
    species_id = db.Column(db.Integer, db.ForeignKey('species.id', ondelete='CASCADE'), index=True)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'), index=True)
    probe = db.Column(db.String(50, collation=SQL_COLLATION), index=True)
    otu_id = db.Column(db.Integer, db.ForeignKey('otus.id', ondelete='CASCADE'), index=True)
    profile = db.deferred(db.Column(db.Text))

    otus = db.relationship('OperationalTaxonomicUnit', backref='otu_profiles', lazy='joined')

    def __init__(self, species_id, study_id, probe, otu_id, profile, normalization_method='numreads'):
        self.species_id = species_id
        self.study_id = study_id
        self.probe = probe
        self.otu_id = otu_id
        self.profile = profile
        self.normalization_method = normalization_method

    def __repr__(self):
        return str(self.id) + ". " + str(self.probe)

    @staticmethod
    def get_profiles(probes, otu_profiles_ids, limit=1000):
        """
        Gets the data for a set of probes (including the full profiles), a limit can be provided to avoid overly
        long queries

        :param species_id: internal id of the species
        :param probes: probe names to fetch
        :param limit: maximum number of probes to get
        :return: List of ExpressionProfile objects including the full profiles
        """
        profiles = OTUProfile.query.\
            options(undefer(OTUProfile.profile)).\
            filter(OTUProfile.otu_id.in_(probes), OTUProfile.id.in_(otu_profiles_ids)).\
            options(joinedload(OTUProfile.otus).load_only(OperationalTaxonomicUnit.original_id)).\
            limit(limit).all()

        return profiles

    @property
    def low_abundance(self, cutoff=10):
        """
        Checks if the mean OTU value in any conditions in the plot is higher than the desired cutoff

        :param cutoff: cutoff for OTU quantification, default = 10
        :return: True in case of low abundance otherwise False
        """
        data = json.loads(self.profile)
        processed_values = OTUProfile.get_values(data)

        checks = [mean(v) > cutoff for _, v in processed_values.items()]

        return not any(checks)

    @staticmethod
    def add_otu_profiles_from_table(feature_table, species_id, study_id, normalization_method='numreads'):
        """
        Function to generate an OTU profile

        :param feature_table: path to the feature table
        :param species_id: internal id of the species
        :param study_id: internal id of the study
        :param normalization_method: method used to normalize the data
        """

        added_otu_profiles = 0

        with open(feature_table, 'r') as fin:

            # read header
            _, *colnames = fin.readline().rstrip().split()

            # build conversion table for runs
            runs = SeqRun.query.filter(SeqRun.accession_number.in_(colnames)).\
                                filter_by(species_id=species_id).\
                                all()
            seq_run_dict = {}
            for r in runs:
                seq_run_dict[r.accession_number] = r.id

            # read each line and build OTU profile
            new_otu_profiles = []

            for line in fin:
                otu_name, *values = line.rstrip().split()

                profile = {'count': {},
                           'sample_id': {},
                           'run_id': {}}

                otu = OperationalTaxonomicUnit.query.filter_by(original_id=otu_name).first()
                
                for c, v in zip(colnames, values):
                    profile['count'][c] = int(float(v))
                    run = SeqRun.query.get(seq_run_dict[c])
                    profile['run_id'][c] = seq_run_dict[c]
                    profile['sample_id'][c] = run.sample_id

                new_profile = OTUProfile(**{"otu_id": otu.id,
                                "probe": otu_name,
                                "species_id": species_id,
                                "study_id": study_id,
                                "normalization_method": normalization_method,
                                "profile": json.dumps({"data": profile})
                                })
                
                new_otu_profiles.append(new_profile)
                added_otu_profiles+=1
                db.session.add(new_profile)

                if len(new_otu_profiles) > 400:
                    db.session.commit()
                    new_otu_profiles = []

            db.session.commit()

            added_otu_profiles_obj = OTUProfile.query.with_entities(OTUProfile.id, OTUProfile.probe).\
                                                         filter(OTUProfile.study_id == study_id,
                                                         OTUProfile.species_id == species_id,
                                                         OTUProfile.normalization_method == normalization_method).all()

            for added_profile in added_otu_profiles_obj:
                for run in runs:
                    new_otu_profile_run = {"otu_profile_id": added_profile.id,
                                            "run_id": run.id}
                    db.session.add(OTUProfileRunAssociation(**new_otu_profile_run))

            db.session.commit()

        return added_otu_profiles