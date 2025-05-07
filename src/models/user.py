"""Data Models for User Entities.

Defines the database tables and relationships for users
"""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlmodel import CheckConstraint, Field, Relationship, SQLModel

from .model_config import ConfiguredBaseModel

# avoids circular dependency by importing at typechecking time. Car and Trip can regular import at runtime
if TYPE_CHECKING:
    from models.car import Car
    from models.trip import Trip


class FriendshipStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    id: uuid.UUID = Field(primary_key=True)
    phone: str | None = Field(default=None, max_length=15)
    firstname: str | None = Field(default=None, max_length=30)
    lastname: str | None = Field(default=None, max_length=30)
    username: str | None = Field(default=None, max_length=30)
    is_onboarded: bool = Field(default=False)
    owned_trips: list["Trip"] = Relationship(back_populates="owner_user")
    owned_cars: list["Car"] = Relationship(back_populates="owner_user")
    friendships_as_user1: list["Friendships"] = Relationship(
        back_populates="user1_obj",
        sa_relationship_kwargs={
            "foreign_keys": "[Friendships.user_id]",
            "primaryjoin": "User.id == Friendships.user_id",
            "lazy": "selectin",
        },
    )

    friendships_as_user2: list["Friendships"] = Relationship(
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


class Friendships(SQLModel, table=True):
    __tablename__ = "friendships"
    __table_args__ = (
        CheckConstraint("user_id < friend_id", name="ck_friendship_order"),
        {"schema": "public"},
    )
    user_id: uuid.UUID = Field(
        foreign_key="public.users.id", primary_key=True, nullable=False
    )
    friend_id: uuid.UUID = Field(
        foreign_key="public.users.id", primary_key=True, nullable=False
    )

    initiator_id: uuid.UUID = Field(foreign_key="public.users.id", nullable=False)

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
    user1_obj: User = Relationship(
        back_populates="friendships_as_user1",
        sa_relationship_kwargs={
            "primaryjoin": "Friendships.user_id == User.id",
            "foreign_keys": "[Friendships.user_id]",
        },
    )
    user2_obj: User = Relationship(
        back_populates="friendships_as_user2",
        sa_relationship_kwargs={
            "primaryjoin": "Friendships.friend_id == User.id",
            "foreign_keys": "[Friendships.friend_id]",
        },
    )


class UserPublic(ConfiguredBaseModel):
    id: uuid.UUID
    phone: str
    firstname: str | None
    lastname: str | None
    is_onboarded: bool


class UserUpdate(ConfiguredBaseModel):
    phone: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    username: str | None = None
