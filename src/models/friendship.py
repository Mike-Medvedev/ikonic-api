"""Data Models for Friendship Entities.

Defines the database tables and relationships for friendships
"""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import Field as PydanticField
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

# avoids circular dependency by importing at typechecking time. Car and Trip can regular import at runtime
if TYPE_CHECKING:
    from models.user import User


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
        foreign_key="user.id",  # Make sure 'user.id' matches your User table and its PK
        nullable=False,
        index=True,  # Good to index foreign keys
    )
    addressee_id: uuid.UUID = Field(
        foreign_key="user.id",  # Make sure 'user.id' matches your User table and its PK
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
        },
    )

    addressee: "User" = Relationship(
        back_populates="friendships_received",
        sa_relationship_kwargs={
            "foreign_keys": "[Friendships.addressee_id]",
        },
    )


class FriendshipPublic(ConfiguredBaseModel):
    id: uuid.UUID
    requester: "User" = PydanticField(validation_alias="requester")
    addressee: "User" = PydanticField(validation_alias="addressee")
    status: FriendshipStatus


class FriendshipCreate(ConfiguredBaseModel):
    addressee_id: uuid.UUID


class FriendshipUpdate(ConfiguredBaseModel):
    status: FriendshipStatus
