from sqlmodel import SQLModel, create_engine

from src.core.config import settings

engine = create_engine(url=str(settings.sqlalchemy_database_uri), echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)
