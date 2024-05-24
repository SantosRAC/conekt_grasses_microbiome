from conekt import db

from sqlalchemy.orm import joinedload, undefer

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

import json

from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit
from conekt.models.seq_run import SeqRun
from conekt.models.relationships_microbiome.otu_profile_run import OTUProfileRunAssociation


class OTUProfile(db.Model):
    __tablename__ = 'otu_profiles'
    id = db.Column(db.Integer, primary_key=True)
    otu_id = db.Column(db.Integer, db.ForeignKey('otus.id', ondelete='CASCADE'), index=True)
    profile = db.deferred(db.Column(db.Text))

    def __init__(self, otu_id, profile):
        self.otu_id = otu_id
        self.profile = profile

    def __repr__(self):
        return str(self.id) + ". " + str(self.otu_id)

    @staticmethod
    def add_otu_profiles_from_table(feature_table, otu_method_id):
        """
        Function to generate an OTU profile

        :param feature_table: path to the feature table
        :param species_id: internal id of the species
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
                           'run': {},
                           'run_id': {}}

                print(otu_name, type(otu_name), '(Remember the \"original OTU ID\" (original_id) is set as a String(255) in the table)\n\n\n\n\n\n\n\n\n')

                otu = OperationalTaxonomicUnit.query.filter_by(original_id=otu_name).first()

                for c, v in zip(colnames, values):
                    profile['count'][c] = int(float(v))
                    profile['run_id'][c] = seq_run_dict[c.upper()]
                    profile['run'][c] = c.upper()

                new_profile = OTUProfile(**{"otu_id": otu.id,
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