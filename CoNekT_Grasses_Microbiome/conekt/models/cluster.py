from conekt import db
from sqlalchemy.orm import undefer
from conekt.models.taxonomy import GTDBTaxon


SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

class Cluster(db.Model):
    __tablename__ = 'cluster'
    id = db.Column(db.Integer, primary_key=True)
    gtdb_id = db.Column(db.String(255), db.ForeignKey('gtdb_taxonomy.id'))

    def __init__(self, id, gtdb_id):
        self.id = id
        self.gtdb_id = gtdb_id

    def __repr__(self):
        return f"{self.id}. {self.gtdb_id}"
    
    @staticmethod
    def add_cluster_from_file(clusters_file):
        """Add clusters from a tabular file to the database.
        
        returns the number of clusters added to the database.
        """
        cluster_count = 0

        # read the genomes file
        with open(clusters_file, 'r') as file:
            # get rid of the header
            _ = file.readline()

            lines = file.readlines()

            for line in lines:
                # split the line into the sample information
                parts = line.strip().split('\t')

                id = int(parts[0])
                gtdb_id = parts[1]
                
                # add the genome to the database
                new_cluster = Cluster(id, gtdb_id)

                db.session.add(new_cluster)
                db.session.commit()
                cluster_count += 1

              
        return cluster_count

