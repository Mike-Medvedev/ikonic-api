from typing import Optional, List
from pydantic import BaseModel
from datetime import date
import uuid
from sqlmodel import Relationship, SQLModel, Field


class DTO[T](BaseModel):
    data: T


class SupabaseUser(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}
    id: uuid.UUID = Field(primary_key=True)


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    id: uuid.UUID = Field(
        primary_key=True, foreign_key="auth.users.id", ondelete="CASCADE")
    phone: str = Field(foreign_key="auth.users.phone")
    firstname: Optional[str]
    lastname: Optional[str]


class TripBase(SQLModel):
    title: str
    start_date: date
    end_date: date
    mountain: str


class Trip(TripBase, table=True):
    __tablename__ = "trips"
    id: Optional[int] = Field(default=None, primary_key=True)
    owner: uuid.UUID
    cars: List["Car"] = Relationship()


class TripCreate(TripBase):
    pass


class TripPublic(TripBase):
    id: int
    owner: uuid.UUID


class TripUpdate(SQLModel):
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    mountain: Optional[str] = None


class TripUserLinkBase(SQLModel):
    rsvp: Optional[str] = None
    paid: Optional[int] = None


class TripUserLink(SQLModel, table=True):
    __tablename__ = "trips_users_map"
    trip_id: int = Field(primary_key=True, foreign_key="trips.id")
    # no need to make fk on supabase auth.users, let db handle
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="auth.users.id")
    rsvp: Optional[str] = None
    paid: Optional[int] = None


class TripUserLinkRsvp(TripUserLinkBase):
    pass


class Rsvp(BaseModel):
    deep_link: str


class InviteCreate(SQLModel):
    user_id: uuid.UUID


class CarBase(SQLModel):
    seat_count: int = 4
    passengers: Optional[List["Passenger"]] = []


class CarCreate(CarBase):
    pass


class CarUpdate(CarBase):
    trip_id: Optional[int]
    owner: Optional[uuid.UUID]
    seat_count: Optional[int] = 4


class Car(SQLModel, table=True):
    __tablename__ = "cars"
    id: Optional[int] = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trips.id", ondelete="CASCADE")
    owner: uuid.UUID = Field(foreign_key="auth.users.id")
    passengers: List["Passenger"] = Relationship(back_populates="car")
    seat_count: int = 4


class CarPublic(CarBase):
    id: int
    trip_id: int
    owner: uuid.UUID


class PassengerBase(SQLModel):
    seat_position: int


class Passenger(PassengerBase, table=True):
    __tablename__ = "passengers"
    user_id: uuid.UUID = Field(
        foreign_key="auth.users.id", primary_key=True, ondelete="CASCADE")
    car_id:  int = Field(foreign_key="cars.id",
                         primary_key=True, ondelete="CASCADE")
    car: Car = Relationship(back_populates="passengers")


class PassengerCreate(PassengerBase):
    # user_id: uuid.UUID
    # car_id: int
    pass


class SortedUsersResponse(BaseModel):
    accepted: List[User] = []
    pending: List[User] = []
    uncertain: List[User] = []
    declined: List[User] = []
