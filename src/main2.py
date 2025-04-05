from fastapi import FastAPI
import uuid

from sqlmodel import create_engine, Session, SQLModel, Field, select


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}
    id: uuid.UUID = Field(primary_key=True)
    aud: str


connection_string = "***REMOVED***"

engine = create_engine(url=connection_string, echo=True)


with Session(engine) as session:
    statement = select(User).where(
        User.aud == "authenticated")
    user = session.exec(statement).first()
    print("-----------------------------")
    print(user)


app = FastAPI()


@app.get("/")
def main():
    return "Hello World"
