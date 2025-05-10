"""Connects to database using connection string and initializes ORM engine."""

from sqlmodel import SQLModel, create_engine

from src.core.config import settings

engine = create_engine(url=str(settings.sqlalchemy_database_uri))


def init_db() -> None:
    """Create Tables in database if they dont exist."""
    SQLModel.metadata.create_all(engine)
