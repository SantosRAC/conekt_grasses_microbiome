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
    probe = db.Column(db.String(50, collation=SQL_COLLATION), index=True)
    otu_id = db.Column(db.Integer, db.ForeignKey('otus.id', ondelete='CASCADE'), index=True)
    profile = db.deferred(db.Column(db.Text))

    otus = db.relationship('OperationalTaxonomicUnit', backref='otu_profiles', lazy='joined')

    def __init__(self, species_id,  probe, otu_id, profile, normalization_method='numreads'):
        self.species_id = species_id
        self.probe = probe
        self.otu_id = otu_id
        self.profile = profile
        self.normalization_method = normalization_method

    def __repr__(self):
        return str(self.id) + ". " + str(self.otu_id)

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
    def add_otu_profiles_from_table(feature_table, species_id, normalization_method='numreads'):
        """
        Function to generate an OTU profile

        :param feature_table: path to the feature table
        :param species_id: internal id of the species
        :param normalization_method: method used to normalize the data
        """

        added_otu_profiles = 0

        # build conversion table for OTUs
        otus = OperationalTaxonomicUnit.query.filter_by().all()
        otu_seq_dict = {}  # key = sequence name uppercase, value internal id
        
        for o in otus:
            otu_seq_dict[o.original_id.upper()] = o.id

        with open(feature_table, 'r') as fin:

            # read header
            _, *colnames = fin.readline().rstrip().split()

            # build conversion table for OTUs
            runs = SeqRun.query.filter(SeqRun.accession_number.in_(colnames)).\
                                all()
            seq_run_dict = {}  # key = sequence name uppercase, value internal id
            for r in runs:
                seq_run_dict[r.accession_number.upper()] = r.id

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
                    run = SeqRun.query.get(seq_run_dict[c.upper()])
                    profile['run_id'][c] = seq_run_dict[c.upper()]
                    profile['sample_id'][c] = run.sample_id

                new_profile = OTUProfile(**{"otu_id": otu.id,
                                "probe": otu_name,
                                "species_id": species_id,
                                "normalization_method": normalization_method,
                                "profile": json.dumps({"data": profile})
                                })
                
                new_otu_profiles.append(new_profile)
                added_otu_profiles+=1
                db.session.add(new_profile)
                db.session.commit()

                for run in runs:
                    new_otu_profile_run = {"otu_profile_id": new_profile.id,
                                           "run_id": run.id}
                    db.session.add(OTUProfileRunAssociation(**new_otu_profile_run))
                
                db.session.commit()

        return added_otu_profiles