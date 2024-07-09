from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class SILVATaxon(db.Model):
    __tablename__ = 'silva_taxonomy'
    id = db.Column(db.Integer, primary_key=True)
    ncbi_taxid = db.Column(db.Integer, db.ForeignKey('ncbi_taxonomy.id', ondelete='SET NULL'), index=True)
    taxon_path = db.Column(db.String(255), default='')
    rank = db.Column(db.String(255), default='')

    def __init__(self, ncbi_taxid, taxon_path, rank):
        self.ncbi_taxid = ncbi_taxid
        self.taxon_path = taxon_path
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

                # check if the taxon is already in the database
                ncbi_record = NCBITaxon.query.filter_by(taxid=int(line[1])).first()

                ncbi_record_id = None

                if ncbi_record:
                    ncbi_record_id = ncbi_record.id

                # add the taxonomy information to the database
                new_taxon = SILVATaxon(**{"taxon_path": line[0],
                                          "ncbi_taxid": ncbi_record_id,
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


class NCBITaxon(db.Model):
    """Table for NCBI taxonomy.

    taxid: NCBI taxonomy ID
    taxonomic_name: Taxonomic name (e.g., Bacteria)
    rank: Rank (e.g., domain)
    division_id: Division ID
    parent_taxid: Parent NCBI taxonomy ID
    
    """
    __tablename__ = 'ncbi_taxonomy'
    id = db.Column(db.Integer, primary_key=True)
    taxid = db.Column(db.Integer, default=0, unique=True)
    taxonomic_name = db.Column(db.String(255), default='')
    rank = db.Column(db.String(255), default='')
    division_id = db.Column(db.Integer, nullable=False)
    parent_taxid = db.Column(db.Integer)

    def __init__(self, taxid, taxonomic_name,
                 rank, division_id, parent_taxid):
        self.taxid = taxid
        self.taxonomic_name = taxonomic_name
        self.rank = rank
        self.division_id = division_id
        self.parent_taxid = parent_taxid
    
    def __repr__(self):
        return str(self.id) + f"({self.taxid}). " + self.taxon

    @staticmethod
    def add_ncbi_taxonomy(ncbi_taxonomy_nodes,
                          ncbi_taxonomy_names,
                          empty=True, filter_ncbi_divisions=[0, 4, 8, 11]):
        """
        Adds NCBI taxonomy information to the database.

        :param ncbi_taxonomy_nodes: NCBI nodes.dmp file
        :param ncbi_taxonomy_names: NCBI names.dmp file
        :param empty: Empty the database first when true (default: True)
        :param filter_ncbi_divisions: Filter NCBI divisions (default: [0, 4, 8, 11],
            which are Bacteria, Plants and Fungi, Unassigned and Environmental samples)
        :return: 
        """

        # If required empty the table first
        if empty:
            try:
                db.session.query(NCBITaxon).delete()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)

        new_taxons = []
        taxon_count = 0

        # read the taxonomy nodes file
        with open(ncbi_taxonomy_nodes, 'r') as file:
            lines = file.readlines()

            for line in lines:

                line = line.strip().split('\t|\t')
                tax_id = line[0]
                parent_tax_id = line[1]
                rank = line[2]
                division_id = line[4]

                # add the NCBI taxonomy information to the database
                # filters the divisions to include only the ones in the list
                if int(division_id) in filter_ncbi_divisions:
                    new_taxon = NCBITaxon(**{"taxid": tax_id,
                                          "taxonomic_name": '',
                                          "rank": rank,
                                          "division_id": division_id,
                                          "parent_taxid": parent_tax_id})

                    db.session.add(new_taxon)
                    new_taxons.append(new_taxon)
                    taxon_count += 1

            # add 400 taxons at the time, more can cause problems with some database engines
            if len(new_taxons) > 400:
                db.session.commit()
                new_taxons = []
        
        # add the last set of taxons
        db.session.commit()

        all_ncbi_taxa = NCBITaxon.query.all()

        taxa_dict = {}

        for t in all_ncbi_taxa:
            taxa_dict[t.taxid] = t

        # read the taxonomy names file
        with open(ncbi_taxonomy_names, 'r') as file:

            for i, line in enumerate(file):

                line = line.strip().split('\t|\t')

                tax_id = int(line[0])
                taxon_name = line[1]
                name_class = line[3].replace('\t|', '')

                if name_class != 'scientific name':
                    continue

                if tax_id in taxa_dict.keys():
                    taxa_dict[tax_id].taxonomic_name = taxon_name
                    print('Added taxon: ' + taxon_name)
                
                if i % 400 == 0:
                    db.session.commit()
                
            db.session.commit()

        return taxon_count

    @staticmethod
    def get_ncbi_taxid_from_taxon(taxon):

        """
        Get the NCBI taxid from a taxon name

        :param taxon: Taxon name
        :return: NCBI taxid
        """

        ncbi_record = NCBITaxon.query.filter_by(taxonomic_name=taxon).first()

        if ncbi_record:
            return ncbi_record
        else:
            return None

    @staticmethod
    def update_counts():
        """
        TODO: implement update counts for NCBI taxonomy
        """

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