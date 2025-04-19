import uuid
from datetime import date

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel


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
        primary_key=True, foreign_key="auth.users.id", ondelete="CASCADE"
    )
    phone: str = Field(foreign_key="auth.users.phone")
    firstname: str | None
    lastname: str | None
    owned_trips: list["Trip"] = Relationship(back_populates="owner_user")
    owned_cars: list["Car"] = Relationship(back_populates="owner_user")


class TripBase(SQLModel):
    title: str
    start_date: date
    end_date: date
    mountain: str


class Trip(TripBase, table=True):
    __tablename__ = "trips"
    id: int | None = Field(default=None, primary_key=True)
    owner: uuid.UUID = Field(foreign_key="public.users.id")
    cars: list["Car"] = Relationship()
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


class DeepLink(BaseModel):
    deep_link: str


class InviteCreate(SQLModel):
    user_id: uuid.UUID


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
    owner_user: User | None = Relationship(back_populates="owned_cars")


class CarPublic(CarBase):
    id: int
    trip_id: int
    owner: User
    passengers: list[User] | None = []
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


class SortedUsersResponse(BaseModel):
    accepted: list[User] = []
    pending: list[User] = []
    uncertain: list[User] = []
    declined: list[User] = []
