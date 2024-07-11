from conekt import db


import os

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

class GenomeENVO(db.Model):
    __tablename__ = 'genome_envo'
    id = db.Column(db.Integer, primary_key=True)
    genome_id = db.Column(db.String(11, collation=SQL_COLLATION), db.ForeignKey('genomes.genome_id'))
    envo_habitat = db.Column(db.String(13, collation=SQL_COLLATION), db.ForeignKey('environment_ontology.envo_term'))
    envo_isolation_source = db.Column(db.String(13, collation=SQL_COLLATION), db.ForeignKey('environment_ontology.envo_term'))
    
    def __init__(self, genome_id, envo_habitat, envo_isolation_source):
        self.genome_id = genome_id
        self.envo_habitat = envo_habitat
        self.envo_isolation_source = envo_isolation_source
    
    def __repr__(self):
        return str(self.id) + ". " + self.genome_id + ". " + self.envo_habitat
    
   