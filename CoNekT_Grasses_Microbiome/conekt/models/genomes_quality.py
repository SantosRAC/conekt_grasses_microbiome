from conekt import db
from sqlalchemy.orm import undefer


SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

class GenomesQuality(db.Model):
    __tablename__ = 'genomes_quality'
    id = db.Column(db.Integer, primary_key=True)
    genome_id = db.Column(db.String(11, collation=SQL_COLLATION), db.ForeignKey('genomes.genome_id', ondelete='NO ACTION'))
    completeness = db.Column(db.Numeric(5,2), nullable=False)
    contamination = db.Column(db.Numeric(5,2), nullable=False)
    quality = db.Column(db.String(15), nullable=False)
    rrna16S = db.Column(db.String(5), nullable=False)
    copies_16s_rrna = db.Column(db.Integer, nullable=False)


    def __init__(self, genome_id, completeness, contamination, quality, rrna16S, copies_16s_rrna):
        self.genome_id = genome_id
        self.completeness = completeness
        self.contamination = contamination
        self.quality = quality
        self.rrna16S = rrna16S
        self.copies_16s_rrna = copies_16s_rrna

    def __repr__(self):
        return f"{self.id}. {self.genome_id} {self.quality}"

    