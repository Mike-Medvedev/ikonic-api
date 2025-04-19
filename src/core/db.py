from sqlmodel import create_engine, SQLModel
from src.core.config import settings


# print(str(settings.SQLALCHEMY_DATABASE_URI))
engine = create_engine(url=str(settings.SQLALCHEMY_DATABASE_URI), echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)
