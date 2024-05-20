from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class SILVATaxon(db.Model):
    __tablename__ = 'silva_taxonomy'
    id = db.Column(db.Integer, primary_key=True)
    ncbi_taxid = db.Column(db.Integer, default=0)
    taxon = db.Column(db.String(255), default='')
    rank = db.Column(db.String(255), default='')

    def __init__(self, ncbi_taxid, taxon, rank):
        self.ncbi_taxid = ncbi_taxid
        self.taxon = taxon
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
                new_taxon = SILVATaxon(**{"taxon": line[0],
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
    def update_counts():
        """
        TODO: implement update counts for NCBI taxonomy
        """
