from sqlmodel import create_engine, SQLModel
from core.config import settings
from models import *


engine = create_engine(url=settings.SQLALCHEMY_DATABASE_URI, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)
