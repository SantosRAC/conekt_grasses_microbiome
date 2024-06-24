from conekt import db

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class Species(db.Model):
    __tablename__ = 'species'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50, collation=SQL_COLLATION), unique=True)
    name = db.Column(db.String(200, collation=SQL_COLLATION))
    data_type = db.Column(db.Enum('genome', 'transcriptome', name='data_type'))
    color = db.Column(db.String(7), default="#C7C7C7")
    highlight = db.Column(db.String(7), default="#DEDEDE")
    sequence_count = db.Column(db.Integer)
    network_count = db.Column(db.Integer)
    profile_count = db.Column(db.Integer)
    description = db.Column(db.Text)
    source = db.Column(db.String(50, collation=SQL_COLLATION))
    literature_id = db.Column(db.Integer, db.ForeignKey('literature.id', ondelete='SET NULL'))
    genome_version = db.Column(db.String(100, collation=SQL_COLLATION))

    samples = db.relationship('Sample', backref='species', lazy='dynamic', cascade="all, delete-orphan", passive_deletes=True)
    sequences = db.relationship('Sequence', backref='species', lazy='dynamic', cascade="all, delete-orphan", passive_deletes=True)
    profiles = db.relationship('ExpressionProfile', backref='species', lazy='dynamic', cascade="all, delete-orphan", passive_deletes=True)

    def __init__(self, code, name, data_type='genome',
                 color="#C7C7C7", highlight="#DEDEDE", description=None, source=None, literature_id=None, genome_version=None):
        self.code = code
        self.name = name
        self.data_type = data_type
        self.color = color
        self.highlight = highlight
        self.sequence_count = 0
        self.profile_count = 0
        self.network_count = 0
        self.description = description
        self.source = source
        self.literature_id = literature_id
        self.genome_version = genome_version

    def __repr__(self):
        return str(self.id) + ". " + self.name

    @property
    def has_cazyme(self):
        from conekt.models.sequences import Sequence
        from conekt.models.relationships.sequence_cazyme import SequenceCAZYmeAssociation

        cazyme = SequenceCAZYmeAssociation.query.join(Sequence, Sequence.id == SequenceCAZYmeAssociation.sequence_id).filter(Sequence.species_id == self.id).first()

        if cazyme is not None:
            return True
        else:
            return False
    
    @property
    def has_interpro(self):
        from conekt.models.sequences import Sequence
        from conekt.models.relationships.sequence_interpro import SequenceInterproAssociation

        domain = SequenceInterproAssociation.query.join(Sequence, Sequence.id == SequenceInterproAssociation.sequence_id).filter(Sequence.species_id == self.id).first()

        if domain is not None:
            return True
        else:
            return False

    @property
    def has_go(self):
        from conekt.models.sequences import Sequence
        from conekt.models.relationships.sequence_go import SequenceGOAssociation

        go = SequenceGOAssociation.query.join(Sequence, Sequence.id == SequenceGOAssociation.sequence_id).filter(Sequence.species_id == self.id).first()

        if go is not None:
            return True
        else:
            return False

    @staticmethod
    def add(code, name, data_type='genome',
            color="#C7C7C7", highlight="#DEDEDE", description=None, source=None, literature_id=None, genome_version=None):

        new_species = Species(code, name, data_type=data_type, color=color, highlight=highlight,
                               description=description, source=source, literature_id=literature_id, genome_version=genome_version)

        species = Species.query.filter_by(code=code).first()

        # species is not in the DB yet, add it
        if species is None:
            try:
                db.session.add(new_species)
                db.session.commit()
            except:
                db.rollback()

            return new_species.id
        else:
            return species.id

    @staticmethod
    def update_counts():
        """
        To avoid long counts the number of sequences, profiles and networks can be precalculated and stored in the
        database using this function.
        """
        from conekt.models.sequences import Sequence

        species = Species.query.all()

        for s in species:
            s.sequence_count = s.sequences.filter(Sequence.type=='protein_coding').count()
            s.profile_count = s.profiles.count()
            s.network_count = s.networks.count()

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
