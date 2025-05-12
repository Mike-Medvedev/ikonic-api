"""Data Models for Friendship Entities.

Defines the database tables and relationships for friendships
"""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import Field as PydanticField
from sqlalchemy import Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlmodel import CheckConstraint, Field, Relationship, SQLModel

from .model_config import ConfiguredBaseModel

# avoids circular dependency by importing at typechecking time. Car and Trip can regular import at runtime
if TYPE_CHECKING:
    from models.user import User


class FriendshipStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


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
    user1_obj: "User" = Relationship(
        back_populates="friendships_as_user1",
        sa_relationship_kwargs={
            "primaryjoin": "Friendships.user_id == User.id",
            "foreign_keys": "[Friendships.user_id]",
        },
    )
    user2_obj: "User" = Relationship(
        back_populates="friendships_as_user2",
        sa_relationship_kwargs={
            "primaryjoin": "Friendships.friend_id == User.id",
            "foreign_keys": "[Friendships.friend_id]",
        },
    )


class FriendshipPublic(ConfiguredBaseModel):
    user: "User" = PydanticField(validation_alias="user1_obj")
    friend: "User" = PydanticField(validation_alias="user2_obj")
    initiator_id: uuid.UUID
    status: FriendshipStatus


class FriendshipCreate(ConfiguredBaseModel):
    user_id: str
    friend_id: str
    initiator_id: str


class FriendshipUpdate(ConfiguredBaseModel):
    user_id: str
    friend_id: str
    status: FriendshipStatus
