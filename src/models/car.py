"""Data models for Car and Passenger entities.

Defines the database tables and relationships for cars used in trips
"""

import uuid
from typing import TYPE_CHECKING, Union

from sqlmodel import Field, Relationship, SQLModel

# avoids circular dependency by importing at runtime
if TYPE_CHECKING:
    from models.user import User


class CarBase(SQLModel):
    seat_count: int = 4
    passengers: list["Passenger"] | None = []


class CarCreate(CarBase):
    pass


class CarUpdate(CarBase):
    trip_id: int | None
    owner: uuid.UUID | None
    seat_count: int | None = 4


class Car(SQLModel, table=True):
    __tablename__ = "cars"
    id: int | None = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trips.id", ondelete="CASCADE")
    owner: uuid.UUID = Field(foreign_key="public.users.id")
    passengers: list["Passenger"] = Relationship(back_populates="car")
    seat_count: int = 4
    owner_user: Union["User", None] = Relationship(back_populates="owned_cars")


class CarPublic(CarBase):
    id: int
    trip_id: int
    owner: "User"
    passengers: list["User"] | None = []
    seat_count: int = 4


class PassengerBase(SQLModel):
    seat_position: int


class Passenger(PassengerBase, table=True):
    __tablename__ = "passengers"
    user_id: uuid.UUID = Field(
        foreign_key="public.users.id", primary_key=True, ondelete="CASCADE"
    )
    car_id: int = Field(foreign_key="cars.id", primary_key=True, ondelete="CASCADE")
    car: Car = Relationship(back_populates="passengers")


class PassengerCreate(PassengerBase):
    pass
