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
    friendships_as_user1: list[Friendships] = Relationship(
        back_populates="user1_obj",
        sa_relationship_kwargs={
            "foreign_keys": "[Friendships.user_id]",
            "primaryjoin": "User.id == Friendships.user_id",
            "lazy": "selectin",
        },
    )

    friendships_as_user2: list[Friendships] = Relationship(
        back_populates="user2_obj",
        sa_relationship_kwargs={
            "foreign_keys": "[Friendships.friend_id]",
            "primaryjoin": "User.id == Friendships.friend_id",
            "lazy": "selectin",
        },
    )

    @property
    def friends(self) -> list["User"]:
        """Returns a list of User objects who are accepted friends.

        Friendships table maps (user1_obj, user2_obj)
        """
        return [
            fs_entry.user1_obj
            for fs_entry in self.friendships_as_user2
            if fs_entry.status == FriendshipStatus.ACCEPTED and fs_entry.user1_obj
        ] + [
            fs_entry.user2_obj
            for fs_entry in self.friendships_as_user1
            if fs_entry.status == FriendshipStatus.ACCEPTED and fs_entry.user2_obj
        ]


class UserPublic(ConfiguredBaseModel):
    id: uuid.UUID
    phone: str
    firstname: str | None
    lastname: str | None
    username: str | None
    rider_type: RiderType | None
    is_onboarded: bool
    avatar_public_url: str | None

    # @field_serializer("avatar_public_url", when_used="unless-none")
    # def cache_bust(self, avatar_public_url: str | None) -> str | None:
    #     """Append a timestamp query param to cache bust."""
    #     if not avatar_public_url:
    #         return None
    #     timestamp = datetime.now()
    #     return f"{avatar_public_url}?t={timestamp}"


class UserUpdate(ConfiguredBaseModel):
    phone: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    username: str | None = None
    rider_type: RiderType | None = None
    avatar_storage_path: str | None = None
