from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


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


class GGTaxon(db.Model):
    __tablename__ = 'gg_taxonomy'
    id = db.Column(db.Integer, primary_key=True)
    gg_id = db.Column(db.Integer, default=0)
    ncbi_taxid = db.Column(db.Integer, db.ForeignKey('ncbi_taxonomy.id', ondelete='SET NULL'), index=True)
    taxon_path = db.Column(db.String(255), default='')

    def __init__(self, gg_id, ncbi_taxid, taxon_path):
        self.gg_id = gg_id
        self.ncbi_taxid = ncbi_taxid
        self.taxon_path = taxon_path
    
    def __repr__(self):
        return str(self.id) + ". " + self.taxon_path
    

    @staticmethod
    def add_gg_taxonomy(gg_taxonomy_data, empty=True):
        """
        Adds GreenGenes taxonomy information to the database.

        :param taxonomy_data: GG taxonomy data (e.g., gg_13_5_taxonomy.txt)
        :param empty: Empty the database first when true (default: True)
        :return: 
        """

        # If required empty the table first
        if empty:
            try:
                db.session.query(GGTaxon).delete()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)

        new_taxons = []
        taxon_count = 0

        # read the taxonomy file
        with open(gg_taxonomy_data, 'r') as file:
            lines = file.readlines()

            for line in lines:

                # split the line into the taxonomy information
                line = line.strip().split('\t')

                lrt = GGTaxon.get_lowest_rank_taxon(line[1])

                ncbi_record = NCBITaxon.get_ncbi_taxid_from_taxon(lrt)

                ncbi_record_id = None

                if ncbi_record:
                    ncbi_record_id = ncbi_record.id

                # add the taxonomy information to the database
                new_taxon = GGTaxon(**{"gg_id": line[0],
                                       "ncbi_taxid": ncbi_record_id,
                                       "taxon_path": line[1]})

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

    @staticmethod
    def get_lowest_rank_taxon(taxon_path):

        """
        Get the lowest rank taxon with information from GreenGenes taxonomy path

        :param taxon_path: Taxon path from GreenGenes taxonomy
        """

        lowest_rank_taxon = {'name': None, 'rank': None}

        phylum_name = taxon_path.split(';')[-6].split('__')[-1]
        class_name = taxon_path.split(';')[-5].split('__')[-1]
        order_name = taxon_path.split(';')[-4].split('__')[-1]
        family_name = taxon_path.split(';')[-3].split('__')[-1]
        genus_name = taxon_path.split(';')[-2].split('__')[-1]
        species_name = taxon_path.split(';')[-1].split('__')[-1]

        if species_name:
            lowest_rank_taxon['name'] = genus_name+' '+species_name
            lowest_rank_taxon['rank'] = 'species'
        elif genus_name:
            lowest_rank_taxon['name'] = genus_name
            lowest_rank_taxon['rank'] = 'genus'
        elif family_name:
            lowest_rank_taxon['name'] = family_name
            lowest_rank_taxon['rank'] = 'family'
        elif order_name:
            lowest_rank_taxon['name'] = order_name
            lowest_rank_taxon['rank'] = 'order'
        elif class_name:
            lowest_rank_taxon['name'] = class_name
            lowest_rank_taxon['rank'] = 'class'
        elif phylum_name:
            lowest_rank_taxon['name'] = phylum_name
            lowest_rank_taxon['rank'] = 'phylum'
        else:
            lowest_rank_taxon['name'] = taxon_path.split(';')[-7]
            lowest_rank_taxon['rank'] = 'kingdom'

        return lowest_rank_taxon['name']

    @staticmethod
    def update_counts():
        """
        TODO: implement update counts for GreenGenes taxonomy
        """