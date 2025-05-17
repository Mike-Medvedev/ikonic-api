"""Data Models for User Entities.

Defines the database tables and relationships for users
"""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlmodel import Field, Relationship, SQLModel

from models.friendship import Friendships, FriendshipStatus

from .model_config import ConfiguredBaseModel

# avoids circular dependency by importing at typechecking time. Car and Trip can regular import at runtime
if TYPE_CHECKING:
    from models.car import Car
    from models.trip import Trip


class RiderType(Enum):
    SKIER = "skier"
    SNOWBOARDER = "snowboarder"


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
    friendships_initiated: list[Friendships] = Relationship(
        back_populates="requester",  # Matches 'requester' attribute in Friendships
        sa_relationship_kwargs={
            "foreign_keys": "[Friendships.requester_id]",
        },
    )

    # Friendships where this user is the addressee
    friendships_received: list[Friendships] = Relationship(
        back_populates="addressee",  # Matches 'addressee' attribute in Friendships
        sa_relationship_kwargs={
            "foreign_keys": "[Friendships.addressee_id]",
        },
    )

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
                        friend=friend_user_public, friendship_id=friendship.id
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
