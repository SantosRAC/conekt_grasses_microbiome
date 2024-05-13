from conekt import db

from sqlalchemy.dialects.mysql import LONGTEXT

SQL_COLLATION = 'NOCASE' if db.engine.name == 'sqlite' else ''

