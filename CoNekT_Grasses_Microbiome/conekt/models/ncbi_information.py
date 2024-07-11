from conekt import db
from sqlalchemy.orm import undefer

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

class NCBI(db.Model):
    __tablename__ = 'ncbi_info'
    id = db.Column(db.Integer, primary_key=True)
    ncbi_accession = db.Column(db.String(15, collation=SQL_COLLATION))
    biosample = db.Column(db.String(12, collation=SQL_COLLATION))
    bioproject = db.Column(db.String(11, collation=SQL_COLLATION))
    genome_id = db.Column(db.String(11, collation=SQL_COLLATION), db.ForeignKey('genomes.genome_id', ondelete='NO ACTION'))

    def __init__(self, genome_id, ncbi_accession, biosample, bioproject):
        self.genome_id = genome_id
        self.ncbi_accession = ncbi_accession
        self.biosample = biosample
        self.bioproject = bioproject

    def __repr__(self):
        return f"{self.id}. {self.genome_id}. {self.ncbi_accession}"

   