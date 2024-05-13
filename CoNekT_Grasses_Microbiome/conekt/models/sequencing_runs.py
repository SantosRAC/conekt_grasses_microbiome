from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

class SeqRun(db.Model):
    __tablename__ = 'sequencing_runs'
    id = db.Column(db.Integer, primary_key=True)
    sra_accession = db.Column(db.String(50, collation=SQL_COLLATION), unique=True)
    layout = db.Column(db.Enum('paired-end', 'single-end', name='RNA-Seq layout'), default='single-end')
    strandness = db.Column(db.Enum('unstranded', 'strand specific', name='RNA-Seq layout'), default='unstranded')
    description = db.Column(db.Text)
    sample_id = db.Column(db.Integer, db.ForeignKey('samples.id', ondelete='CASCADE'), index=True)
    
    def __init__(self, sra_accession, layout, strandness,
                 sample_id, description):
        self.sra_accession = sra_accession
        self.layout = layout
        self.strandness = strandness
        self.sample_id = sample_id
        self.description = description
    
    def __repr__(self):
        return str(self.id) + ". " + self.sra_accession (self.sample_id)
