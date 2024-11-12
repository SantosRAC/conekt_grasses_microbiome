from conekt import db
from sqlalchemy.orm import undefer
from conekt.models.literature import LiteratureItem
from conekt.models.cluster import Cluster
from conekt.models.genomes_quality import GenomesQuality
from conekt.models.geographic_genomes_information import Geographic
from conekt.models.genome_envo import GenomeENVO
from conekt.models.ncbi_information import NCBI
from conekt.models.geocode_utils import geocode_location

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class Genome(db.Model):
    __tablename__ = 'genomes'
    genome_id = db.Column(db.String(11, collation=SQL_COLLATION), primary_key=True)
    genome_type = db.Column(db.String(7, collation=SQL_COLLATION), nullable=False)
    length = db.Column(db.Integer, nullable = False)
    N50 = db.Column(db.Integer, nullable = False)
    gc_perc = db.Column(db.Numeric(5,2), nullable=False)
    num_contigs = db.Column(db.Integer, nullable=False)
    cluster_id = db.Column(db.Integer, db.ForeignKey('cluster.id'), index=True)
    representative = db.Column(db.String(5), nullable=False)
    literature_id = db.Column(db.Integer, db.ForeignKey('literature.id', ondelete='NO ACTION'), index=True)

    def __init__(self, genome_id, genome_type, length, N50, gc_perc, num_contigs, cluster_id, representative, literature_id):
        self.genome_id = genome_id
        self.genome_type = genome_type
        self.length = length
        self.N50 = N50
        self.gc_perc = gc_perc
        self.num_contigs = num_contigs
        self.cluster_id = cluster_id
        self.representative = representative
        self.literature_id = literature_id

    def __repr__(self):
        return f"{self.genome_id}. {self.genome_type}"
    
    
    @staticmethod
    def add_genomes_from_file(genomes_file):
        """Add genomes from a tabular file to the database.
        
        returns the number of genomes added to the database.
        """
        genome_count = 0

        # read the genomes file
        with open(genomes_file, 'r') as file:
            # get rid of the header
            _ = file.readline()

            lines = file.readlines()

            for line in lines:
                # split the line into the genome information
                parts = line.strip().split('\t')

                genome_id = parts[0]
                doi = parts[1]
                genome_type = parts[2]
                length = int(parts[3])
                N50 = int(parts[4])
                gc_perc = float(parts[5])
                num_contigs = int(parts[6])
                cluster_id = int(parts[7])
                representative = parts[8]
                completeness = float(parts[9])
                contamination = float(parts[10])
                quality = parts[11]
                rrna_16S = parts[12]
                copies_16S_rrna = parts[13]
                country = parts[14]
                local = parts[15]
                lat = parts[16]
                lon = parts[17]

                # get the ontology terms, if they exist. Habitat
                try:
                    envo_habitat = parts[18]
                except IndexError:
                    envo_habitat = None
                    print("Warning: ENVO term not found for this sample")

                # get the ontology terms, if they exist. Habitat
                try:
                    envo_isolation_source = parts[19]
                except IndexError:
                    envo_isolation_source = None
                    print("Warning: ENVO term not found for this sample")

                ncbi_accession = parts[20]
                biosample = parts[21]
                bioproject = parts[22]               

                # Check for existing genome entry
                existing_genome = Genome.query.filter_by(genome_id=genome_id).first()

                if existing_genome:
                    print(f"Genome {genome_id} already exists in the database, skipping...")
                    continue

                if doi.lower() == 'unpublished':
                    literature_id = None  # or any other indicator for unpublished
                else:
                    literature = LiteratureItem.query.filter_by(doi=doi).first()

                    if literature is None:
                        literature_id = LiteratureItem.add(doi)
                    else:
                        literature_id = literature.id

                # add the genome to the database
                new_genome = Genome(genome_id, genome_type, length, N50, gc_perc, num_contigs, cluster_id, representative, literature_id)
                db.session.add(new_genome)

                 # add the genome quality to the database
                new_genome_quality_info = GenomesQuality(genome_id, completeness, contamination, quality, rrna_16S, copies_16S_rrna)
                db.session.add(new_genome_quality_info)

                # add the geographic information to the database

                # Tratamento das coordenadas
                if not lat or not lon:
                # Chama a função de geocodificação com country e local (se disponível)
                    lat, lon = geocode_location(country, local)
                if not lat or not lon:
                    print(f"Geocoding failed for {local}, {country}. No coordinates found.")
                    lat = None
                    lon = None


                new_geographic_info = Geographic(genome_id, country, local, lat, lon)

                db.session.add(new_geographic_info)
               
                # add the genome to the database
                new_genome_envo = GenomeENVO(genome_id, envo_habitat, envo_isolation_source)
                db.session.add(new_genome_envo)

                # add NCBI information to the database
                new_ncbi_information = NCBI(genome_id, ncbi_accession, biosample, bioproject)
                db.session.add(new_ncbi_information)

                db.session.commit()
                genome_count += 1

            
        return genome_count
