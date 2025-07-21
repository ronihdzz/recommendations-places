from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from core.settings import settings


application_name = settings.PROJECT.NAME.replace(" ", "-").lower()
engine = create_engine(
    settings.POSTGRESQL_URL.unicode_string(), connect_args={"application_name": application_name}, poolclass=NullPool
)
SessionLocal = sessionmaker(autocommit=False, bind=engine)


@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
