from functools import lru_cache
from typing import Annotated, Generator
from sqlmodel import Session
from fastapi import Depends
from vonage import Auth, Vonage
from src.core.db import engine
from src.core.config import settings


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


@lru_cache(maxsize=1)  # caches instance creating a singleton
def get_vonage_client() -> Vonage:
    return Vonage(Auth(
        api_key=settings.VONAGE_API_KEY,
        api_secret=settings.VONAGE_API_SECRET)
    )
