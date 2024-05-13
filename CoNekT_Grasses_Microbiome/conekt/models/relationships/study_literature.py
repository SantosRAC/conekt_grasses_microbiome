from conekt import db


class StudyLiteratureAssociation(db.Model):
    __tablename__ = 'study_literature'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id', ondelete='CASCADE'), nullable=False)
    literature_id = db.Column(db.Integer, db.ForeignKey('literature.id', ondelete='CASCADE'), nullable=False)

    def __init__(self, study_id, literature_id):
        self.study_id = study_id
        self.literature_id = literature_id
    
    def __repr__(self):
        return f'{self.study_id} - {self.literature_id}'