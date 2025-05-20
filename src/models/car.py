"""Data models for Car and Passenger entities.

Defines the database tables and relationships for cars used in trips
"""

import uuid

from sqlmodel import Field, Relationship, SQLModel, text

from models.user import User, UserPublic

from .model_config import ConfiguredBaseModel


class CarBase(ConfiguredBaseModel):
    seat_count: int = 4
    passengers: list["Passenger"] = Field(default_factory=list)


class CarCreate(CarBase):
    pass


class CarUpdate(CarBase):
    trip_id: uuid.UUID | None
    owner: uuid.UUID | None
    seat_count: int | None = 4


class Car(SQLModel, table=True):
    __tablename__ = "cars"
    __table_args__ = {"schema": "public"}
    id: uuid.UUID = Field(
        default=None,
        primary_key=True,
        index=True,
        nullable=False,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    trip_id: uuid.UUID = Field(
        foreign_key="public.trips.id", nullable=False, ondelete="CASCADE"
    )
    owner: uuid.UUID = Field(foreign_key="public.users.id", nullable=False)
    seat_count: str | None = Field(default=None, nullable=True)
    owner_user: User = Relationship(back_populates="owned_cars")
    passengers: list["Passenger"] = Relationship(back_populates="car")


class CarPublic(CarBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    owner: UserPublic
    passengers: list[UserPublic] = Field(default_factory=list)
    seat_count: int = 4


class PassengerBase(ConfiguredBaseModel):
    user_id: uuid.UUID
    seat_position: int


class Passenger(SQLModel, table=True):
    __tablename__ = "passengers"
    __table_args__ = {"schema": "public"}
    user_id: uuid.UUID = Field(
        foreign_key="public.users.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )
    car_id: uuid.UUID = Field(
        foreign_key="public.cars.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )
    seat_position: int | None = Field(default=None)
    car: Car = Relationship(back_populates="passengers")


class PassengerPublic(PassengerBase):
    user_id: uuid.UUID
    car_id: uuid.UUID
    seat_position: int


class PassengerCreate(PassengerBase):
    pass
