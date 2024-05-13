from conekt import db



SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''


class OperationalPhylogeneticUnit(db.Model):
    __tablename__ = 'opus'
    id = db.Column(db.Integer, primary_key=True)
    
    method_id = db.Column(db.Integer, db.ForeignKey('opu_methods.id', ondelete='CASCADE'), index=True)

    def __init__(self, method_id):
        self.method_id = method_id
    
    def __repr__(self):
        return str(self.id) + ". " + self.method_id

    @staticmethod
    def add_opus():
        
        #TODO: implement function