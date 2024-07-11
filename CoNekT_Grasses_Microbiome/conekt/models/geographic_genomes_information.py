from conekt import db
from sqlalchemy.orm import undefer


SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

class Geographic(db.Model):
    __tablename__ = 'geographic_info'
    id = db.Column(db.Integer, primary_key=True)
    genome_id = db.Column(db.String(11, collation=SQL_COLLATION), db.ForeignKey('genomes.genome_id', ondelete='NO ACTION'))
    country = db.Column(db.String(50, collation=SQL_COLLATION))
    local = db.Column(db.String(500, collation=SQL_COLLATION))
    lat = db.Column(db.Numeric(9,6))
    lon = db.Column(db.Numeric(9,6))

    

    def __init__(self, genome_id, country, local, lat, lon):
        self.genome_id = genome_id
        self.country = country
        self.local = local
        self.lat = lat
        self.lon = lon

    def __repr__(self):
        return f"{self.id}. {self.genome_id}. {self.country}"

    