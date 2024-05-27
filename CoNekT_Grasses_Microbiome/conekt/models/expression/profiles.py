from conekt import db
from conekt.models.sequences import Sequence
from conekt.models.condition_tissue import ConditionTissue
from conekt.models.sample import Sample
from conekt.models.seq_run import SeqRun
from conekt.models.ontologies import PlantOntology, PlantExperimentalConditionsOntology

import json
import contextlib
from collections import defaultdict
from statistics import mean
from math import log

from sqlalchemy.orm import joinedload, undefer
from flask import url_for, abort

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class ExpressionProfile(db.Model):
    __tablename__ = 'expression_profiles'
    id = db.Column(db.Integer, primary_key=True)
    normalization_method = db.Column(db.Enum('numreads', 'cpm', 'tpm', 'tmm'), default='tpm')
    species_id = db.Column(db.Integer, db.ForeignKey('species.id', ondelete='CASCADE'), index=True)
    probe = db.Column(db.String(50, collation=SQL_COLLATION), index=True)
    sequence_id = db.Column(db.Integer, db.ForeignKey('sequences.id', ondelete='CASCADE'), index=True)
    profile = db.deferred(db.Column(db.Text))

    specificities = db.relationship('ExpressionSpecificity',
                                    backref=db.backref('profile', lazy='joined'),
                                    lazy='dynamic',
                                    cascade="all, delete-orphan",
                                    passive_deletes=True)

    def __init__(self, species_id, probe, sequence_id, profile, normalization_method='tpm'):
        self.species_id = species_id
        self.probe = probe
        self.sequence_id = sequence_id
        self.profile = profile
        self.normalization_method = normalization_method

    @staticmethod
    def get_values(data):
        """
        Gets an object for values in data

        :param data: Dict with expression profile
        :return: Object of ontologies and values
        """
        processed_values = {}
        for key, expression_values in data["data"]["exp_value"].items():
            po_value = data["data"]["PO_class"][key]

            if po_value not in processed_values:
                processed_values[po_value] = []

            processed_values[po_value].append(expression_values)
        
        return processed_values


    @staticmethod
    def __profile_to_table(data):
        """
        Internal function to convert an expression profile (dict) to a tabular text

        :param data: Dict with expression profile
        :return: table (string)
        """
        output = [["condition", "mean", "min", "max"]]
        order = data["order"]
        processed_values = ExpressionProfile.get_values(data)

        for o in order:
            try:
                values = processed_values[o]
                output.append([o,
                               str(mean(values)),
                               str(min(values)),
                               str(max(values))
                               ])
            except Exception as e:
                print(e)

        return '\n'.join(['\t'.join(l) for l in output])

    @property
    def table(self):
        """
        Returns the condition expression as a tabular text file

        :return: table with data (string)
        """
        table = ExpressionProfile.__profile_to_table(json.loads(self.profile))

        return table

    def tissue_table(self, condition_tissue_id, use_means=True):
        """
        Returns the tissue expression as a tabular text file

        :param condition_tissue_id: condition_tissue_id for the conversion
        :param use_means: Use the mean of the condition (recommended)
        :return: table with data (string)
        """
        table = ExpressionProfile.__profile_to_table(self.tissue_profile(condition_tissue_id,
                                                                         use_means=use_means)
                                                     )
        return table

    @property
    def low_abundance(self, cutoff=10):
        """
        Checks if the mean expression value in any conditions in the plot is higher than the desired cutoff

        :param cutoff: cutoff for expression, default = 10
        :return: True in case of low abundance otherwise False
        """
        data = json.loads(self.profile)
        processed_values = ExpressionProfile.get_values(data)

        checks = [mean(v) > cutoff for _, v in processed_values.items()]

        return not any(checks)

    @staticmethod
    def convert_profile(condition_to_tissue, profile_data, use_means=True):
        """
        Convert a full, detailed profile into a more general summarized one using conversion table stored in the
        database

        :param condition_to_tissue: dict with conversion instructions
        :param profile_data: profile to convert
        :param use_means: use means of detailed condition if True otherwise use samples independently. Default True
        :return: New profile
        """
        tissues = list(set(condition_to_tissue['conversion'].values()))

        output = {}

        for t in tissues:
            valid_conditions = [k for k in profile_data['data'] if k in condition_to_tissue['conversion'] and condition_to_tissue['conversion'][k] == t]
            valid_values = []
            for k, v in profile_data['data'].items():
                if k in valid_conditions:
                    if use_means:
                        valid_values.append(mean(v))
                    else:
                        valid_values += v

            output[t] = valid_values if len(valid_values) > 0 else [0]

        return {'order': condition_to_tissue['order'],
                'colors': condition_to_tissue['colors'],
                'data': output}

    def tissue_profile(self, condition_tissue_id, use_means=True):
        """
        Applies a conversion to the profile, grouping several condition into one more general feature (e.g. tissue).

        :param condition_tissue_id: identifier of the conversion table
        :param use_means: store the mean of the condition rather than individual values. The matches the spm
        calculations better.
        :return: parsed profile
        """
        ct = ConditionTissue.query.get(condition_tissue_id)

        condition_to_tissue = json.loads(ct.data)
        profile_data = json.loads(self.profile)

        output = ExpressionProfile.convert_profile(condition_to_tissue, profile_data, use_means=use_means)

        return output

    @staticmethod
    def get_heatmap(species_id, probes, zlog=True, raw=False):
        """
        Returns a heatmap for a given species (species_id) and a list of probes. It returns a dict with 'order'
        the order of the experiments and 'heatmap' another dict with the actual data. Data is zlog transformed

        :param species_id: species id (internal database id)
        :param probes: a list of probes to include in the heatmap
        :param zlog: enable zlog transformation (otherwise normalization against highest expressed condition)
        """
        profiles = ExpressionProfile.query.options(undefer('profile')).filter_by(species_id=species_id).\
            filter(ExpressionProfile.probe.in_(probes)).all()

        order = []

        output = []

        not_found = [p.lower() for p in probes]

        for profile in profiles:
            name = profile.probe
            data = json.loads(profile.profile)
            order = data['order']
            experiments = data['data']['exp_value']

            with contextlib.suppress(ValueError):
                not_found.remove(profile.probe.lower())

            with contextlib.suppress(ValueError):
                not_found.remove(profile.sequence.name.lower())
            
            processed_values = ExpressionProfile.get_values(data)

            values = {}

            for o in order:
                values[o] = mean(processed_values[o])

            row_mean = mean(values.values())
            row_max = max(values.values())

            for o in order:
                if zlog:
                    if row_mean == 0 or values[o] == 0:
                        values[o] = '-'
                    else:
                        try:
                            values[o] = log(values[o]/row_mean, 2)
                        except ValueError as _:
                            print("Unable to calculate log()", values[o], row_mean)
                            values[o] = '-'
                else:
                    if row_max != 0 and not raw:
                        values[o] = values[o]/row_max

            output.append({"name": name,
                           "values": values,
                           "sequence_id": profile.sequence_id,
                           "shortest_alias": profile.sequence.shortest_alias})

        if len(not_found) > 0:
            flash("Couldn't find profile for: %s" % ", ".join(not_found), "warning")

        return {'order': order, 'heatmap_data': output}

    @staticmethod
    def get_po_heatmap(species_id, probes, pos, zlog=True, raw=False):
        """
        Returns a heatmap for a given species (species_id), a list of probes and a list of ontologies. It returns a dict with 'order'
        the order of the experiments and 'heatmap' another dict with the actual data. Data is zlog transformed

        :param species_id: species id (internal database id)
        :param probes: a list of probes to include in the heatmap
        :param pos: a list of po classes to include in the heatmap
        :param zlog: enable zlog transformation (otherwise normalization against highest expressed condition)
        """
        profiles = ExpressionProfile.query.options(undefer('profile')).filter_by(species_id=species_id).\
            filter(ExpressionProfile.probe.in_(probes)).all()

        order = []

        output = []

        not_found = [p.lower() for p in probes]

        for profile in profiles:
            name = profile.probe
            data = json.loads(profile.profile)
            if pos:
                order = pos
            else:
                order = data['order']
                
            experiments = data['data']['exp_value']


            with contextlib.suppress(ValueError):
                not_found.remove(profile.probe.lower())

            with contextlib.suppress(ValueError):
                not_found.remove(profile.sequence.name.lower())
            
            values = {}
            labels = []

            for o in order:
                for key, value in data['data']['PO_class'].items():
                    if value == o:
                        values[key] = data['data']['exp_value'][key] 
                        labels.append(key + " ("+ o +")")

            row_max = max(list(values.values()))

            for v in values:
                if zlog:
                    if values[v] == 0:
                        values[v] = '-'
                    else:
                        try:
                            values[v] = log(values[v], 2)
                        except ValueError as _:
                            print("Unable to calculate log()", values[v])
                            values[v] = '-'
                else:
                    if row_max != 0 and not raw:
                        values[v] = values[v]/row_max

            output.append({"name": name,
                           "values": values,
                           "sequence_id": profile.sequence_id,
                           "shortest_alias": profile.sequence.shortest_alias})

        if len(not_found) > 0:
            flash("Couldn't find profile for: %s" % ", ".join(not_found), "warning")

        return {'labels':labels, 'order': order, 'heatmap_data': output}

    @staticmethod
    def get_profiles(species_id, probes, limit=1000):
        """
        Gets the data for a set of probes (including the full profiles), a limit can be provided to avoid overly
        long queries

        :param species_id: internal id of the species
        :param probes: probe names to fetch
        :param limit: maximum number of probes to get
        :return: List of ExpressionProfile objects including the full profiles
        """
        profiles = db.session.query(ExpressionProfile).\
            options(undefer(ExpressionProfile.profile)).\
            filter(ExpressionProfile.probe.in_(probes)).\
            filter_by(species_id=species_id).\
            options(joinedload(ExpressionProfile.sequence).load_only(Sequence.name).noload(Sequence.xrefs)).\
            limit(limit).all()

        return profiles

    @staticmethod
    def add_profile_from_lstrap(matrix_file, annotation_file, species_id, normalization_method='tpm'):
        """
        Function to convert an (normalized) expression matrix (lstrap output) into a profile

        :param matrix_file: path to the expression matrix
        :param annotation_file: path to the file assigning samples to conditions
        :param species_id: internal id of the species
        :param normalization_method: method used for normalization (default TPM)
        """
        annotation = {}

        with open(annotation_file, 'r') as fin:
            # get rid of the header
            _ = fin.readline()

            for line in fin:
                parts = line.strip().split('\t')
                if len(parts) == 6:
                    run, sample, literature_doi, strandness, layout, seq_platform = parts
                    run_in_matrix = SeqRun.query.filter_by(accession_number=run).first()
                    run_sample = Sample.query.filter_by(name=sample).first()

                    if run_sample and run_in_matrix:
                        annotation[run] = {}
                        annotation[run]["literature_doi"] = literature_doi
                        annotation[run]["sample_id"] = run_sample.id

                    else:
                        print("Either sample or run (or both) not found: ", sample, run)
                        exit(1)

                else:
                    print("Annotation file not in expected format")
                    exit(1)

        # build conversion table for sequences
        sequences = Sequence.query.filter_by(species_id=species_id, type="protein_coding").all()
        sequence_dict = {}  # key = sequence name uppercase, value internal id
        for s in sequences:
            sequence_dict[s.name.upper()] = s.id

        with open(matrix_file) as fin:
            # read header
            _, *colnames = fin.readline().rstrip().split()

            colnames = [c.replace('.htseq', '') for c in colnames]

            # read each line and build profile
            new_probes = []
            for line in fin:
                transcript, *values = line.rstrip().split()
                profile = {'exp_value': {},
                           'literature_doi': {},
                           'sample_id': {}}

                for c, v in zip(colnames, values):
                    if c in annotation.keys():
                        profile['exp_value'][c] = float(v)
                        profile['literature_doi'][c] = annotation[c]['literature_doi']
                        profile['sample_id'][c] = annotation[c]['sample_id']

                new_probe = ExpressionProfile(**{"species_id": species_id,
                                "normalization_method": normalization_method,
                                "probe": transcript,
                                "sequence_id": sequence_dict[transcript.upper()] if transcript.upper() in sequence_dict.keys() else None,
                                "profile": json.dumps({'data': profile})}
                            )

                new_probes.append(new_probe)
                db.session.add(new_probe)

                if len(new_probes) > 400:
                    db.session.commit()
                    new_probes = []

            db.session.commit()