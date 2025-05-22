"""Data Models for User Entities.

Defines the database tables and relationships for users
"""

import re
import uuid
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import field_validator
from sqlalchemy import Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlmodel import Field, Relationship, SQLModel

from models.friendship import Friendships, FriendshipStatus

from .model_config import ConfiguredBaseModel

MIN_PHONE_NUMBER_LENGTH = 10
MAX_PHONE_NUMBER_LENGTH = 16

# avoids circular dependency by importing at typechecking time. Car and Trip can regular import at runtime
if TYPE_CHECKING:
    from models.car import Car
    from models.trip import Trip


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
    is_onboarded: bool = Field(default=False)
    avatar_storage_path: str | None = Field(default=None)
    avatar_public_url: str | None = Field(default=None)
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

                friend_user_public = User.model_validate(
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
                friend_user_public = User.model_validate(
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
