from typing import Optional, List
from datetime import date
import uuid
from sqlmodel import Relationship, SQLModel, Field


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}
    id: uuid.UUID = Field(primary_key=True)


class Trip(SQLModel, table=True):
    __tablename__ = "trips"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    start_date: date
    end_date: date
    mountain: str
    cars: List["Car"] = Relationship()


class TripUserLink(SQLModel, table=True):
    __tablename__ = "trips_users_map"
    trip_id: int = Field(primary_key=True, foreign_key="trip.id")
    # no need to make fk on supabase auth.users, let db handle
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="user.id")
    rsvp: str
    paid: int


class Car(SQLModel, table=True):
    __tablename__ = "cars"
    id: Optional[int] = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trips.id", ondelete="CASCADE")
    owner: uuid.UUID = Field(foreign_key="user.id")
    passengers: List["Passenger"] = Relationship()
    seat_count: int


class Passenger(SQLModel, table=True):
    __tablename__ = "passengers"
    user_id: uuid.UUID = Field(foreign_key="auth.users.id", primary_key=True)
    car_id:  int = Field(foreign_key="cars.id",
                         primary_key=True, ondelete="CASCADE")
    seat_position: int
