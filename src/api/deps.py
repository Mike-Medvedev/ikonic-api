from typing import Annotated, Generator
from sqlmodel import Session
from fastapi import Depends
from core.db import engine


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDb = Annotated[Session, Depends(get_db)]
