from conekt import db

from conekt.models.seq_run import SeqRun
from conekt.models.literature import LiteratureItem


class RunLitAssociation(db.Model):
    __tablename__ = 'run_literature'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('sequencing_runs.id', ondelete='CASCADE'))
    literature_id = db.Column(db.Integer, db.ForeignKey('literature.id', ondelete='CASCADE'))
    species_id = db.Column(db.Integer, db.ForeignKey('species.id', ondelete='CASCADE'))
    data_type = db.Column(db.Enum('rnaseq', 'metataxonomics', name='data_type'))

    literature_information = db.relationship('LiteratureItem', backref=db.backref('run_lit_associations',
                                                              lazy='dynamic',
                                                              passive_deletes=True), lazy='joined')

    def __init__(self, run_id, literature_id, species_id, data_type):
        self.run_id = run_id
        self.literature_id = literature_id
        self.species_id = species_id
        self.data_type = data_type
    
    @staticmethod
    def add_run_lit_association(run_name, lit_doi, species_id, data_type):

        run = SeqRun.query.filter_by(sra_accession=run_name,
                                     data_type=data_type).first()
        literature_item = LiteratureItem.query.filter_by(doi=lit_doi).first()

        if literature_item is None:
            literature_id = LiteratureItem.add(lit_doi)
            literature_item = LiteratureItem.query.filter_by(id=literature_id).first()
        
        association = {'run_id': run.id,
                       'literature_id': literature_item.id,
                       'species_id': species_id,
                       'data_type': data_type}
    
        db.engine.execute(RunLitAssociation.__table__.insert(), association)