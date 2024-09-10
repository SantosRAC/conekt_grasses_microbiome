from conekt import db

from sqlalchemy.orm import undefer
import operator
import sys

from conekt.models.literature import LiteratureItem
from conekt.models.relationships.sample_group import SampleGroupAssociation

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

class Sample(db.Model):
    __tablename__ = 'samples'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80, collation=SQL_COLLATION), unique=True)
    description = db.Column(db.Text)
    replicate = db.Column(db.Integer, default=1)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id', ondelete='CASCADE'), index=True)
    species_genotype = db.Column(db.String(100, collation=SQL_COLLATION))
    literature_id = db.Column(db.Integer, db.ForeignKey('literature.id', ondelete='CASCADE'), index=True)
    
    def __init__(self, name, description, species_id,
                 species_genotype, literature_id, replicate = 1):
        self.name = name
        self.description = description
        self.species_id = species_id
        self.species_genotype = species_genotype
        self.literature_id = literature_id
        self.replicate = replicate
    
    def __repr__(self):
        return str(self.id) + ". " + self.name (self.species_id)

    @staticmethod
    def add_samples_from_file(samples_file, species_id):
        """Add samples from a tabular file to the database.
        
        returns the number of samples added to the database.
        """

        from conekt.models.ontologies import PlantExperimentalConditionsOntology
        from conekt.models.ontologies import PlantOntology
        from conekt.models.ontologies import EnvironmentOntology

        sample_count = 0

        # read the samples file
        with open(samples_file, 'r') as file:
            # get rid of the header
            _ = file.readline()

            lines = file.readlines()

            for line in lines:
                
                # split the line into the sample information
                parts = line.strip().split('\t')

                sample_name = parts[0]
                doi = parts[1]
                condition_description = parts[2]
                replicate = int(parts[3])

                # get the ontology terms, if they exist
                try:
                    po_anatomy_term = parts[4]
                except IndexError:
                    po_anatomy_term = None
                    print("Warning: PO term not found for this sample")

                try:
                    po_dev_stage_term = parts[5]
                except IndexError:
                    po_dev_stage_term = None
                    print("Warning: PO term not found for this sample")

                try:
                    peco_term = parts[6]
                except IndexError:
                    peco_term = None
                    print("Warning: PECO term not found for this sample")

                try:
                    envo_term = parts[7]
                except IndexError:
                    envo_term = None
                    print("Warning: ENVO term not found for this sample")
                
                try:
                    species_genotype = parts[8]
                except IndexError:
                    species_genotype = None
                    print("Warning: Genotype term not found for this sample")

                literature = LiteratureItem.query.filter_by(doi=doi).first()

                if literature is None:
                    literature_id = LiteratureItem.add(doi)
                else:
                    literature_id = literature.id

                # add the sample to the database
                new_sample = Sample(sample_name,
                                   condition_description,
                                   species_id,
                                   species_genotype,
                                   literature_id,
                                   replicate)

                db.session.add(new_sample)
                db.session.commit()
                sample_count += 1

                try:
                    sample_group_definitions = parts[9]
                    sample_groups = sample_group_definitions.split(';')
                    for sample_group in sample_groups:
                        group_type, group_name = sample_group.split(':')
                        if group_type.startswith(' '):
                            group_type = group_type.replace(' ', '', 1)
                        sample_group_association = SampleGroupAssociation(new_sample.id, group_type, group_name)
                        db.session.add(sample_group_association)
                        db.session.commit()
                except IndexError:
                    sample_group_definitions = None
                    print("Warning: Group(s) was/were not defined for this sample")

                if po_anatomy_term:
                    if po_anatomy_term.startswith('PO:'):
                        PlantOntology.add_sample_po_association(new_sample.id, po_anatomy_term)

                if po_dev_stage_term:
                    if po_dev_stage_term.startswith('PO:'):
                        PlantOntology.add_sample_po_association(new_sample.id, po_dev_stage_term)
                
                if peco_term:
                    if peco_term.startswith('PECO:'):
                        PlantExperimentalConditionsOntology.add_sample_peco_association(new_sample.id, peco_term)
                
                if envo_term:
                    if envo_term.startswith('ENVO:'):
                        EnvironmentOntology.add_sample_envo_association(new_sample.id, envo_term)

        return sample_count
