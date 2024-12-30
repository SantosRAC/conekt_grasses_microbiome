from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class SILVATaxon(db.Model):
    __tablename__ = 'silva_taxonomy'
    id = db.Column(db.Integer, primary_key=True)
    ncbi_taxid = db.Column(db.Integer)
    taxon_path = db.Column(db.String(255), default='')
    rank = db.Column(db.String(255), default='')

    def __init__(self, taxon_path, ncbi_taxid, rank):
        self.taxon_path = taxon_path
        self.ncbi_taxid = ncbi_taxid
        self.rank = rank
    
    def __repr__(self):
        return str(self.id) + ". " + self.taxon

    @staticmethod
    def add_silva_taxonomy(silva_taxonomy_data, empty=True):
        """
        Adds SILVA taxonomy information to the database.

        :param taxonomy_data: SILVA taxonomy data (e.g., tax_slv_ssu_138.txt)
        :param empty: Empty the database first when true (default: True)
        :return: 
        """

        # If required empty the table first
        if empty:
            try:
                db.session.query(SILVATaxon).delete()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)

        new_taxons = []
        taxon_count = 0

        # read the taxonomy file
        with open(silva_taxonomy_data, 'r') as file:
            lines = file.readlines()

            for line in lines:

                # split the line into the taxonomy information
                # Columns 4 and 5 are not used (remark and release)
                line = line.strip().split('\t')

                # add the taxonomy information to the database
                new_taxon = SILVATaxon(**{"taxon_path": line[0],
                                          "ncbi_taxid": line[1],
                                          "rank": line[2]})

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
    def update_counts():
        """
        TODO: implement update counts for SILVA taxonomy
        """


class GTDBTaxon(db.Model):
    """Table for GTDB taxonomy.

    taxid: GTDB taxonomy ID
    taxon_path: Taxon path  
    """
    __tablename__ = 'gtdb_taxonomy'
    id = db.Column(db.Integer, primary_key=True)
    gtdb_id = db.Column(db.String(255), default='')
    taxon_path = db.Column(db.String(255), default='')

    def __init__(self, gtdb_id, taxon_path):
        self.gtdb_id = gtdb_id
        self.taxon_path = taxon_path

    def __init__(self, gtdb_id, taxon_path):
        self.gtdb_id = gtdb_id
        self.taxon_path = taxon_path

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
            lines = file.readlines()

            for line in lines:

                # split the line into the taxonomy information
                line = line.strip().split('\t')

                # add the taxonomy information to the database
                new_taxon = GTDBTaxon(**{"gtdb_id": line[0],
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


class GGTaxon(db.Model):
    __tablename__ = 'gg_taxonomy'
    id = db.Column(db.Integer, primary_key=True)
    gg_id = db.Column(db.Integer, default=0)
    taxon_path = db.Column(db.String(255), default='')

    def __init__(self, gg_id, taxon_path):
        self.gg_id = gg_id
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

                # add the taxonomy information to the database
                new_taxon = GGTaxon(**{"gg_id": line[0],
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