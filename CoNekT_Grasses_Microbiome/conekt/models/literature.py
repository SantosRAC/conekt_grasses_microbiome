import datetime
from conekt import db
from crossref.restful import Works

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

class LiteratureItem(db.Model):
    __tablename__ = 'literature'
    id = db.Column(db.Integer, primary_key=True)
    qtd_author = db.Column(db.Integer, nullable=False)
    author_names = db.Column(db.String(100, collation=SQL_COLLATION), nullable=False)
    title = db.Column(db.String(250, collation=SQL_COLLATION), nullable=False)
    public_year = db.Column(db.Integer, nullable=False)
    doi = db.Column(db.String(100, collation=SQL_COLLATION), nullable=False, unique=True)

    def __init__(self, qtd_author, author_names, title, public_year, doi):
        self.qtd_author = qtd_author
        self.author_names = author_names
        self.title = title
        self.public_year = public_year
        self.doi = doi

    def __repr__(self):
        return str(self.id) + ". " + (f'{self.author_names} ({self.public_year})')

    # adding literature data in the DB
    @staticmethod
    def add(doi):
        if doi.lower() == 'unpublished':
            # Criar um objeto literature com os valores padrão para 'unpublished'
            qtd_author = 0
            author_names = 'Unpublished'
            title = 'Unpublished'
            public_year = datetime.datetime.now().year  # ou outro valor padrão
        else:
            works = Works()
            # verify if DOI already exists in DB, if not, collect data
            literature_info = works.doi(doi)

            if literature_info is None:
                print(f"Warning: No information found for DOI {doi}.")
                qtd_author = 0
                author_names = 'Unknown'
                title = 'Unknown'
                public_year = '2024'  # ou outro valor padrão
            else:
                qtd_author = len(literature_info.get('author', []))
                if 'family' in literature_info['author'][0].keys():
                    author_names = literature_info['author'][0]['family']
                else:
                    author_names = literature_info['author'][0]['name']
                title = literature_info['title'][0] if literature_info.get('title') else 'Unknown'
                if 'published-print' in literature_info.keys():
                    public_year = literature_info['published-print']['date-parts'][0][0]
                elif 'published-online' in literature_info.keys():
                    public_year = literature_info['published-online']['date-parts'][0][0]
                else:
                    public_year = literature_info['issued']['date-parts'][0][0]

        new_literature = LiteratureItem(qtd_author, author_names, title, public_year, doi)

        literature = LiteratureItem.query.filter_by(doi=doi).first()

        # literature is not in the DB yet, add it
        if literature is None:
            try:
                db.session.add(new_literature)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)
            return new_literature.id
        else:
            return literature.id