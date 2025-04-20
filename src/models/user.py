"""Data Models for User Entities.

Defines the database tables and relationships for users
"""

import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

# avoids circular dependency by importing at runtime
if TYPE_CHECKING:
    from models.car import Car
    from models.trip import Trip


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "public", "extend_existing": True}
    id: uuid.UUID = Field(
        primary_key=True, foreign_key="auth.users.id", ondelete="CASCADE"
    )
    phone: str = Field(foreign_key="auth.users.phone")
    firstname: str | None
    lastname: str | None
    owned_trips: list["Trip"] = Relationship(back_populates="owner_user")
    owned_cars: list["Car"] = Relationship(back_populates="owner_user")
