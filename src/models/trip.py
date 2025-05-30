"""Data Models for Trip Entities.

Defines the database tables and relationships for trips in trip planning.
"""

import uuid
from datetime import date

from sqlmodel import Field, Relationship, SQLModel, text

from models.car import Car
from models.user import User, UserPublic

from .model_config import ConfiguredBaseModel


class TripBase(ConfiguredBaseModel):
    title: str
    start_date: date
    end_date: date
    mountain: str
    desc: str | None = None


class Trip(SQLModel, table=True):
    __tablename__ = "trips"
    __table_args__ = {"schema": "public"}

    id: uuid.UUID = Field(
        default=None,
        primary_key=True,
        index=True,
        nullable=False,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )

    owner: uuid.UUID = Field(
        foreign_key="public.users.id", nullable=False, ondelete="CASCADE"
    )
    title: str = Field(nullable=False)
    start_date: date = Field(nullable=False)
    end_date: date = Field(nullable=False)
    mountain: str = Field(max_length=50, nullable=False)
    desc: str | None = Field(default=None)
    trip_image_storage_path: str | None = Field(default=None)
    owner_user: User = Relationship(back_populates="owned_trips")
    cars: list[Car] = Relationship()


class TripCreate(TripBase):
    pass


class TripUpdate(ConfiguredBaseModel):
    title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    mountain: str | None = None
    desc: str | None = None
    trip_image_storage_path: str | None = None


class TripPublic(TripBase):
    id: uuid.UUID
    owner: UserPublic
    trip_image_storage_path: str | None
