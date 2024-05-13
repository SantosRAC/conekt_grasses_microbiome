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

sequence_family = db.Table('sequence_family',
                           db.Column('id', db.Integer, primary_key=True),
                           db.Column('sequence_id', db.Integer, db.ForeignKey('sequences.id'), index=True),
                           db.Column('gene_family_id', db.Integer, db.ForeignKey('gene_families.id'), index=True)
                           )

sequence_coexpression_cluster = \
    db.Table('sequence_coexpression_cluster',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('sequence_id', db.Integer, db.ForeignKey('sequences.id'), index=True),
             db.Column('coexpression_cluster_id', db.Integer, db.ForeignKey('coexpression_clusters.id'), index=True)
             )

coexpression_cluster_similarity = \
    db.Table('coexpression_cluster_similarity',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('source_id', db.Integer, db.ForeignKey('coexpression_clusters.id'), index=True),
             db.Column('target_id', db.Integer, db.ForeignKey('coexpression_clusters.id'), index=True)
             )

sequence_xref = db.Table('sequence_xref',
                         db.Column('id', db.Integer, primary_key=True),
                         db.Column('sequence_id', db.Integer, db.ForeignKey('sequences.id'), index=True),
                         db.Column('xref_id', db.Integer, db.ForeignKey('xrefs.id'), index=True)
                         )

sequence_sequence_ecc = db.Table('sequence_sequence_ecc',
                                 db.Column('id', db.Integer, primary_key=True),
                                 db.Column('query_id', db.Integer, db.ForeignKey('sequences.id'), index=True),
                                 db.Column('target_id', db.Integer, db.ForeignKey('sequences.id'), index=True)
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

cluster_go_enrichment = db.Table('cluster_go_enrichment',
                                 db.Column('id', db.Integer, primary_key=True),
                                 db.Column('cluster_id', db.Integer, db.ForeignKey('coexpression_clusters.id'), index=True),
                                 db.Column('go_id', db.Integer, db.ForeignKey('go.id'), index=True)
                                 )

cluster_clade_enrichment = db.Table('cluster_clade_enrichment',
                                    db.Column('id', db.Integer, primary_key=True),
                                    db.Column('cluster_id', db.Integer, db.ForeignKey('coexpression_clusters.id'), index=True),
                                    db.Column('clade_id', db.Integer, db.ForeignKey('clades.id'), index=True),
                                    db.Column('gene_family_method_id', db.Integer,
                                              db.ForeignKey('gene_family_methods.id'), index=True)
                                    )
