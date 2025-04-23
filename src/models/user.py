"""Data Models for User Entities.

Defines the database tables and relationships for users
"""

import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .model_config import ConfiguredBaseModel

# avoids circular dependency by importing at typechecking time. Car and Trip can regular import at runtime
if TYPE_CHECKING:
    from models.car import Car
    from models.trip import Trip


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "public", "extend_existing": True}
    id: uuid.UUID = Field(primary_key=True)
    phone: str = Field()
    firstname: str | None
    lastname: str | None
    owned_trips: list["Trip"] = Relationship(back_populates="owner_user")
    owned_cars: list["Car"] = Relationship(back_populates="owner_user")


class UserPublic(ConfiguredBaseModel):
    id: uuid.UUID
    phone: str
    firstname: str | None
    lastname: str | None
