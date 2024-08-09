"""
Tables to be used to define many-to-many relations. In case additional parameters are defined on the relationship, an
additional model needs to be created that extends these.
"""

from conekt import db

sample_po = db.Table('sample_po',
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('sample_id', db.Integer, db.ForeignKey('samples.id'), index=True),
                     db.Column('po_id', db.Integer, db.ForeignKey('plant_ontology.id'), index=True),
                     db.Column('species_id', db.Integer, db.ForeignKey('species.id'), index=True)
                    )

sequence_go = db.Table('sequence_go',
                       db.Column('id', db.Integer, primary_key=True),
                       db.Column('sequence_id', db.Integer, db.ForeignKey('sequences.id'), index=True),
                       db.Column('go_id', db.Integer, db.ForeignKey('go.id'), index=True)
                       )

sequence_interpro = db.Table('sequence_interpro',
                             db.Column('id', db.Integer, primary_key=True),
                             db.Column('sequence_id', db.Integer, db.ForeignKey('sequences.id'), index=True),
                             db.Column('interpro_id', db.Integer, db.ForeignKey('interpro.id'), index=True),
                             )

sequence_cazyme = db.Table('sequence_cazyme',
                            db.Column('id', db.Integer, primary_key=True),
                            db.Column('sequence_id', db.Integer, db.ForeignKey('sequences.id'), index=True),
                            db.Column('cazyme_id', db.Integer, db.ForeignKey('cazyme.id'), index=True)
                            )