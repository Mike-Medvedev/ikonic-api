from sqlmodel import create_engine, SQLModel
from models import *


connection_string = "***REMOVED***"

engine = create_engine(url=connection_string, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)
