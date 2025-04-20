"""Data Models for Trip Entities.

Defines the database tables and relationships for trips in trip planning.
"""

import uuid
from datetime import date

from sqlmodel import Field, Relationship, SQLModel

from models.car import Car
from models.user import User


class TripBase(SQLModel):
    title: str
    start_date: date
    end_date: date
    mountain: str


class Trip(TripBase, table=True):
    __tablename__ = "trips"
    id: int | None = Field(default=None, primary_key=True)
    owner: uuid.UUID = Field(foreign_key="public.users.id")
    cars: list[Car] = Relationship()
    owner_user: User | None = Relationship(back_populates="owned_trips")


class TripCreate(TripBase):
    pass


class TripPublic(TripBase):
    id: int
    owner: User


class TripUpdate(SQLModel):
    title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    mountain: str | None = None


class TripUserLinkBase(SQLModel):
    rsvp: str | None = None
    paid: int | None = None


class TripUserLink(SQLModel, table=True):
    __tablename__ = "trips_users_map"
    trip_id: int = Field(primary_key=True, foreign_key="trips.id")
    # no need to make fk on supabase auth.users, let db handle
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="public.users.id")
    rsvp: str | None = None
    paid: int | None = None


class TripUserLinkRsvp(TripUserLinkBase):
    pass
