"""Data Models for Trip Entities.

Defines the database tables and relationships for trips in trip planning.
"""

import uuid
from datetime import date

from sqlmodel import Field, Relationship, SQLModel

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
    id: int | None = Field(default=None, primary_key=True)
    owner: uuid.UUID = Field(foreign_key="public.users.id")
    title: str
    start_date: date
    end_date: date
    mountain: str
    desc: str | None = None
    cars: list[Car] = Relationship()
    owner_user: User = Relationship(back_populates="owned_trips")


class TripCreate(TripBase):
    pass


class TripUpdate(ConfiguredBaseModel):
    title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    mountain: str | None = None
    desc: str | None = None


class TripPublic(TripBase):
    id: int
    owner: UserPublic


class TripParticipationBase(ConfiguredBaseModel):
    rsvp: str | None = None
    paid: int | None = None


class TripParticipation(SQLModel, table=True):
    __tablename__ = "trips_users_map"
    trip_id: int = Field(primary_key=True, foreign_key="trips.id")
    rsvp: str | None = Field(default=None)
    paid: int | None = None
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="public.users.id")


class TripParticipationRsvp(TripParticipationBase):
    pass
