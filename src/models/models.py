"""Collection of domain models and SQLAlchemy Tables.

These models represent real world objects and what they mean to our system.
"""

import re
import uuid
from datetime import date
from enum import Enum
from typing import Literal

from pydantic import Field as PydanticField
from pydantic import field_validator
from sqlalchemy import Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlmodel import (
    CheckConstraint,
    Field,
    Index,
    Relationship,
    SQLModel,
    column,
    func,
    text,
)

from .model_config import ConfiguredBaseModel

MIN_PHONE_NUMBER_LENGTH = 10
MAX_PHONE_NUMBER_LENGTH = 16


# ============================================================================
# FRIENDSHIP MODELS
# ============================================================================
"""Data Models for Friendship Entities.

Defines the database tables and relationships for friendships
"""


class FriendshipStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class FriendRequestType(str, Enum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"


class Friendships(SQLModel, table=True):
    __tablename__ = "friendships"

    __table_args__ = (
        CheckConstraint(text("requester_id <> addressee_id")),
        # Note: PostgreSQL might auto-generate a name if you omit `name`.
        # Providing a name ensures consistency. Your DDL implies an auto-generated name.
        # If you want SQLModel to not specify a name, omit the `name` argument.
        # CREATE UNIQUE INDEX unique_friendship_pair
        # ON Friendships (LEAST(requester_id, addressee_id), GREATEST(requester_id, addressee_id));
        Index(
            "unique_friendship_pair",
            func.least(column("requester_id"), column("addressee_id")),
            func.greatest(
                column("requester_id"), column("addressee_id")
            ),  # Corrected order of args if it was swapped
            unique=True,
        ),
        {"schema": "public"},
    )
    id: uuid.UUID | None = Field(
        primary_key=True,
        index=True,  # Good to index PKs
        nullable=False,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )

    requester_id: uuid.UUID = Field(
        foreign_key="public.users.id",
        nullable=False,
        index=True,  # Good to index foreign keys
    )
    addressee_id: uuid.UUID = Field(
        foreign_key="public.users.id",
        nullable=False,
        index=True,  # Good to index foreign keys
    )

    status: FriendshipStatus = Field(
        default=FriendshipStatus.PENDING,
        sa_column=Column(
            SQLAlchemyEnum(
                FriendshipStatus,  # Pass your Python enum class directly
                name="friendship_status",  # Matches your PG ENUM catalog type name
                create_constraint=True,  # For non-native enums; for native, it might be ignored or useful
                native_enum=True,  # Crucial for PostgreSQL to use the native ENUM type
                values_callable=lambda obj: [
                    e.value for e in obj
                ],  # Ensures it uses the .value attribute
            )
        ),
    )
    requester: "User" = Relationship(
        back_populates="friendships_initiated",
        sa_relationship_kwargs={
            "foreign_keys": "[Friendships.requester_id]",
            "primaryjoin": "Friendships.requester_id == User.id ",
            "lazy": "selectin",
        },
    )

    addressee: "User" = Relationship(
        back_populates="friendships_received",
        sa_relationship_kwargs={
            "foreign_keys": "[Friendships.addressee_id]",
            "primaryjoin": "Friendships.addressee_id == User.id",
            "lazy": "selectin",
        },
    )


class FriendshipPublic(ConfiguredBaseModel):
    id: uuid.UUID
    requester: "UserPublic" = PydanticField(validation_alias="requester")
    addressee: "UserPublic" = PydanticField(validation_alias="addressee")
    status: FriendshipStatus


class FriendshipCreate(ConfiguredBaseModel):
    addressee_id: uuid.UUID


class FriendshipUpdate(ConfiguredBaseModel):
    status: FriendshipStatus


# ============================================================================
# INVITATION & RSVP MODELS
# ============================================================================
"""Data Models for Invite Entities.

Defines the database tables and relationships for inviting and Rsvping to trips.
"""


class RegisteredInvitee(ConfiguredBaseModel):
    type: Literal["registered"] = "registered"
    user_id: uuid.UUID = Field(alias="userId")


class ExternalInvitee(ConfiguredBaseModel):
    type: Literal["external"] = "external"
    phone_number: str = Field(alias="phoneNumber")

    @field_validator("phone_number", mode="before")
    @classmethod
    def validate_phone(cls, v: str) -> str | None:
        return clean_and_validate_phone(v)


Invitee = RegisteredInvitee | ExternalInvitee


class InvitationEnum(str, Enum):
    ACCEPTED = "accepted"
    PENDING = "pending"
    UNCERTAIN = "uncertain"
    DECLINED = "declined"


class InvitationCreate(ConfiguredBaseModel):
    invitees: list[Invitee]


class InviteUserPayload(InvitationCreate):
    trip_id: uuid.UUID = Field(alias="tripId")


class AttendanceList(ConfiguredBaseModel):
    accepted: list["UserPublic"]
    pending: list["UserPublic"]
    uncertain: list["UserPublic"]
    declined: list["UserPublic"]


class InvitationBatchResponseData(ConfiguredBaseModel):
    all_invites_processed_successfully: bool
    sms_failures_count: int = 0
    sms_phone_number_failures: list[str] = Field(default_factory=list)


class Invitation(SQLModel, table=True):
    __tablename__ = "invitations"
    __table_args__ = (
        Index(
            "unique_invitation_registered_user",
            "trip_id",
            "user_id",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        Index(
            "unique_invitation_external_user",
            "trip_id",
            "registered_phone",
            unique=True,
            postgresql_where=text("registered_phone IS NOT NULL"),
        ),
        {"schema": "public"},
    )

    id: uuid.UUID = Field(
        primary_key=True,
        index=True,
        nullable=False,
    )
    trip_id: uuid.UUID = Field(
        foreign_key="public.trips.id", nullable=False, ondelete="CASCADE"
    )
    user_id: uuid.UUID | None = Field(
        foreign_key="public.users.id", default=None, nullable=True, ondelete="CASCADE"
    )
    claim_user_id: uuid.UUID | None = Field(default=None, nullable=True)
    registered_phone: str | None = Field(default=None, nullable=True)
    rsvp: InvitationEnum | None = Field(
        default=InvitationEnum.PENDING,
        sa_column=Column(
            SQLAlchemyEnum(
                InvitationEnum,  # Pass your Python enum class directly
                name="invitationenum",  # Matches your PG ENUM catalog type name
                create_constraint=True,  # For non-native enums; for native, it might be ignored or useful
                native_enum=True,  # Crucial for PostgreSQL to use the native ENUM type
                values_callable=lambda obj: [
                    e.value for e in obj
                ],  # Ensures it uses the .value attribute
            )
        ),
    )
    paid: int | None = Field(default=None)

    @field_validator("registered_phone", mode="before")
    @classmethod
    def validate_phone(cls, v: str) -> str | None:
        return clean_and_validate_phone(v)


class InvitationUpdate(ConfiguredBaseModel):
    invite_token: str
    rsvp: InvitationEnum


# ============================================================================
# TRIP MODELS
# ============================================================================
"""Data Models for Trip Entities.

Defines the database tables and relationships for trips in trip planning.
"""


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
    owner_user: "User" = Relationship(back_populates="owned_trips")
    cars: list["Car"] = Relationship()


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
    owner: "UserPublic"
    trip_image_storage_path: str | None


# ============================================================================
# USER MODELS
# ============================================================================
"""Data Models for User Entities.

Defines the database tables and relationships for users
"""


class RiderType(Enum):
    SKIER = "skier"
    SNOWBOARDER = "snowboarder"


def clean_and_validate_phone(phone: str | None) -> str | None:
    """Clean phone number by removing non-digits and validate format."""
    if phone is None:
        return None

    cleaned = re.sub(r"[^\d]", "", str(phone))

    if not cleaned:
        return None

    if len(cleaned) < MIN_PHONE_NUMBER_LENGTH or len(cleaned) > MAX_PHONE_NUMBER_LENGTH:
        raise ValueError(
            f"Phone number must be between 10-15 digits, got {len(cleaned)}"
        )

    return cleaned


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    id: uuid.UUID = Field(primary_key=True)
    phone: str | None = Field(default=None, max_length=15)
    firstname: str | None = Field(default=None, max_length=30)
    lastname: str | None = Field(default=None, max_length=30)
    username: str | None = Field(default=None, max_length=30)
    is_onboarded: bool = Field(default=False, nullable=True)
    rider_type: RiderType | None = Field(
        default=None,
        sa_column=Column(
            SQLAlchemyEnum(
                RiderType,  # Pass your Python enum class directly
                name="rider_type",  # Matches your PG ENUM catalog type name
                create_constraint=True,  # For non-native enums; for native, it might be ignored or useful
                native_enum=True,  # Crucial for PostgreSQL to use the native ENUM type
                values_callable=lambda obj: [
                    e.value for e in obj
                ],  # Ensures it uses the .value attribute
            )
        ),
    )
    avatar_public_url: str | None = Field(default=None)
    avatar_storage_path: str | None = Field(default=None)
    owned_trips: list["Trip"] = Relationship(back_populates="owner_user")
    owned_cars: list["Car"] = Relationship(back_populates="owner_user")

    # Friendships where this user is the requester
    friendships_initiated: list["Friendships"] = Relationship(
        back_populates="requester",
        sa_relationship_kwargs={
            "foreign_keys": "[Friendships.requester_id]",
            "primaryjoin": "User.id == Friendships.requester_id",
            "lazy": "selectin",
        },
    )

    # Friendships where this user is the addressee
    friendships_received: list["Friendships"] = Relationship(
        back_populates="addressee",
        sa_relationship_kwargs={
            "foreign_keys": "[Friendships.addressee_id]",
            "primaryjoin": "User.id == Friendships.addressee_id",
            "lazy": "selectin",
        },
    )

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: str) -> str | None:
        return clean_and_validate_phone(v)

    @property
    def friends_with_details(self) -> list["UserWithFriendshipInfo"]:
        """Returns a list of friends, each with their User object and the
        ID of the friendship record.
        """
        detailed_friends: list[UserWithFriendshipInfo] = []

        # Iterate through friendships initiated by this user
        for friendship in self.friendships_initiated:
            if (
                friendship.status == FriendshipStatus.ACCEPTED
                and friendship.addressee
                and friendship.id
            ):
                # Convert the ORM User (friendship.addressee) to UserPublic Pydantic model
                # This requires UserPublic to be importable and configured for from_orm/model_validate

                friend_user_public = UserPublic.model_validate(
                    friendship.addressee
                )  # Pydantic v2

                detailed_friends.append(
                    UserWithFriendshipInfo(
                        user=friend_user_public, friendship_id=friendship.id
                    )
                )

        # Iterate through friendships received by this user
        for friendship in self.friendships_received:
            if (
                friendship.status == FriendshipStatus.ACCEPTED
                and friendship.requester
                and friendship.id
            ):
                friend_user_public = UserPublic.model_validate(
                    friendship.requester
                )  # Pydantic v2

                detailed_friends.append(
                    UserWithFriendshipInfo(
                        user=friend_user_public, friendship_id=friendship.id
                    )
                )

        return detailed_friends


class UserPublic(ConfiguredBaseModel):
    id: uuid.UUID
    phone: str
    firstname: str | None
    lastname: str | None
    username: str | None
    rider_type: RiderType | None
    is_onboarded: bool
    avatar_public_url: str | None

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: str) -> str | None:
        return clean_and_validate_phone(v)


class UserWithFriendshipInfo(ConfiguredBaseModel):
    user: UserPublic
    friendship_id: uuid.UUID


class UserUpdate(ConfiguredBaseModel):
    phone: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    username: str | None = None
    rider_type: RiderType | None = None
    avatar_storage_path: str | None = None

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: str) -> str | None:
        return clean_and_validate_phone(v)


# ============================================================================
# CAR & PASSENGER MODELS
# ============================================================================
"""Data models for Car and Passenger entities.

Defines the database tables and relationships for cars used in trips
"""


class CarBase(ConfiguredBaseModel):
    seat_count: int = 4
    passengers: list["UserPublic"] = Field(default_factory=list)


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
    seat_count: int = Field(default=4, nullable=False)
    owner_user: "User" = Relationship(back_populates="owned_cars")
    passengers: list["Passenger"] = Relationship(back_populates="car")


class CarPublic(CarBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    owner: "UserPublic"
    passengers: list["UserPublic"] = Field(default_factory=list)
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
    car: "Car" = Relationship(back_populates="passengers")


class PassengerPublic(PassengerBase):
    user_id: uuid.UUID
    car_id: uuid.UUID
    seat_position: int


class PassengerCreate(PassengerBase):
    pass
