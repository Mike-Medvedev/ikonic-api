from typing import Optional
from fastapi import FastAPI
import uuid
from datetime import date

from sqlmodel import create_engine, Session, SQLModel, Field, select, MetaData


metadata_obj = MetaData(schema="public")


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}
    id: uuid.UUID = Field(primary_key=True)
    aud: str


class Trips(SQLModel, table=True):
    metadata = metadata_obj
    __tablename__ = "trips"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    start_date: date
    end_date: date


connection_string = "***REMOVED***"

engine = create_engine(url=connection_string)

trip1 = Trips(title="New Trip!", start_date=date.today(),
              end_date=date.today())


# with Session(engine) as session:
#     session.add(trip1)
#     session.commit()
#     # statement = select(Trips)
#     # q = session.exec(statement).first()
#     # print(q)
with Session(engine) as session:
    statement = select(Trips)
    q = session.exec(statement).first()
    print(q)

app = FastAPI()


@app.get("/")
def main():
    return "Hello World"
