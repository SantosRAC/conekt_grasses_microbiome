from conekt import db, whooshee

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

@whooshee.register_model('id', 'taxon_path', 'domain', 'phylum', 'Class', 'order', 'family', 'genus', 'species')
class GTDBTaxon(db.Model):
    """Table for GTDB taxonomy.

    taxid: GTDB taxonomy ID
    taxon_path: Taxon path  
    """
    __tablename__ = 'gtdb_taxonomy'
    id = db.Column(db.String(30, collation=SQL_COLLATION), primary_key=True)
    taxon_path = db.Column(db.String(255), default='')
    domain = db.Column(db.String(255), default='')
    phylum = db.Column(db.String(255), default='')
    Class = db.Column(db.String(255), default='')
    order = db.Column(db.String(255), default='')
    family = db.Column(db.String(255), default='')
    genus = db.Column(db.String(255), default='')
    species = db.Column(db.String(255), default='')


    def __init__(self, id, taxon_path, domain, phylum, Class, order, family, genus, species):
        self.id = id
        self.taxon_path = taxon_path
        self.domain = domain
        self.phylum = phylum
        self.Class = Class
        self.order = order
        self.family = family
        self.genus = genus
        self.species = species

    @staticmethod
    def add_gtdb_taxonomy(gtdb_taxonomy_data, empty=True):
        """
        Adds GTDB taxonomy information to the database.

        :param taxonomy_data: GTDB taxonomy data (e.g., bac120_taxonomy_r220.tsv, for Bacteria)
        :param empty: Empty the database first when true (default: True)
        :return: 
        """

        # If required empty the table first
        if empty:
            try:
                db.session.query(GTDBTaxon).delete()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)

        new_taxons = []
        taxon_count = 0

        # read the taxonomy file
        with open(gtdb_taxonomy_data, 'r') as file:
            _ = file.readline()

            lines = file.readlines()

            for line in lines:

                # split the line into the taxonomy information
                parts = line.strip().split('\t')

                gtdb_id = parts[0]
                taxon_path = parts[1]
                domain = parts[2]
                phylum = parts[3]
                Class = parts[4]
                order = parts[5]
                family = parts[6]
                genus = parts[7]
                species = parts[8]


                 # add the taxonomy information to the database

                new_taxon = GTDBTaxon(gtdb_id, taxon_path, domain, phylum, Class, order, family, genus, species)

                db.session.add(new_taxon)
                new_taxons.append(new_taxon)
                taxon_count += 1

            # add 400 taxons at the time, more can cause problems with some database engines
            if len(new_taxons) > 400:
                db.session.commit()
                new_taxons = []

        # add the last set of sequences
        db.session.commit()

        return taxon_count
