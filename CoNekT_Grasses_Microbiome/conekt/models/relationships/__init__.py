"""
Tables to be used to define many-to-many relations. In case additional parameters are defined on the relationship, an
additional model needs to be created that extends these.
"""

from conekt import db

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

sequence_family = db.Table('sequence_family',
                           db.Column('id', db.Integer, primary_key=True),
                           db.Column('sequence_id', db.Integer, db.ForeignKey('sequences.id'), index=True),
                           db.Column('gene_family_id', db.Integer, db.ForeignKey('gene_families.id'), index=True)
                           )

sequence_xref = db.Table('sequence_xref',
                         db.Column('id', db.Integer, primary_key=True),
                         db.Column('sequence_id', db.Integer, db.ForeignKey('sequences.id'), index=True),
                         db.Column('xref_id', db.Integer, db.ForeignKey('xrefs.id'), index=True)
                         )

sequence_sequence_clade = db.Table('sequence_sequence_clade',
                                   db.Column('id', db.Integer, primary_key=True),
                                   db.Column('sequence_one_id', db.Integer, db.ForeignKey('sequences.id'), index=True),
                                   db.Column('sequence_two_id', db.Integer, db.ForeignKey('sequences.id'), index=True)
                                   )

family_xref = db.Table('family_xref',
                       db.Column('id', db.Integer, primary_key=True),
                       db.Column('gene_family_id', db.Integer, db.ForeignKey('gene_families.id'), index=True),
                       db.Column('xref_id', db.Integer, db.ForeignKey('xrefs.id'), index=True)
                       )

family_go = db.Table('family_go',
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('gene_family_id', db.Integer, db.ForeignKey('gene_families.id'), index=True),
                     db.Column('go_id', db.Integer, db.ForeignKey('go.id'), index=True)
                     )

family_interpro = db.Table('family_interpro',
                           db.Column('id', db.Integer, primary_key=True),
                           db.Column('gene_family_id', db.Integer, db.ForeignKey('gene_families.id'), index=True),
                           db.Column('interpro_id', db.Integer, db.ForeignKey('interpro.id'), index=True)
                           )

family_cazyme = db.Table('family_cazyme',
                        db.Column('id', db.Integer, primary_key=True),
                        db.Column('gene_family_id', db.Integer, db.ForeignKey('gene_families.id'), index=True),
                        db.Column('cazyme_id', db.Integer, db.ForeignKey('cazyme.id'), index=True)
                        )
