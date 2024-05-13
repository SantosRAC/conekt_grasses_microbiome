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

    
    """
    __tablename__ = 'ncbi_taxonomy'
    id = db.Column(db.Integer, primary_key=True)
    taxid = db.Column(db.Integer, default=0, unique=True)
    taxon = db.Column(db.String(255), default='')
    rank = db.Column(db.String(255), default='')
    parent_taxid = db.Column(db.Integer, db.ForeignKey('ncbi_taxonomy.id', ondelete='CASCADE'))

    def __init__(self, taxid, taxon, rank, parent_taxid):
        self.taxid = taxid
        self.taxon = taxon
        self.rank = rank
        self.parent_taxid = parent_taxid
    
    def __repr__(self):
        return str(self.id) + f"({self.taxid}). " + self.taxon

    @staticmethod
    def update_counts():
        """
        TODO: implement update counts for NCBI taxonomy
        """


class NCBITaxonName(db.Model):
    """Table for NCBI taxonomy names.

    Stores the names of the NCBI taxonomy.
    """
    __tablename__ = 'ncbi_taxonomy_names'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), default='')

    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return str(self.id) + ". " + self.name

    @staticmethod
    def update_counts():
        """
        TODO: implement update counts for NCBI taxonomy
        """
