"""Data Models for Invite Entities.

Defines the database tables and relationships for inviting and Rsvping to trips.
"""

import uuid
from enum import Enum

from pydantic import Field
from sqlalchemy import Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlmodel import SQLModel, text

from models.trip import TripParticipationCreate
from models.user import UserPublic

from .model_config import ConfiguredBaseModel


class InvitationEnum(str, Enum):
    ACCEPTED = "accepted"
    PENDING = "pending"
    UNCERTAIN = "uncertain"
    DECLINED = "declined"


class InvitationCreate(ConfiguredBaseModel):
    invites: list[TripParticipationCreate]
    deep_link: str = Field(alias="deepLink")


class AttendanceList(ConfiguredBaseModel):
    accepted: list[UserPublic]
    pending: list[UserPublic]
    uncertain: list[UserPublic]
    declined: list[UserPublic]


class InvitationBatchResponseData(ConfiguredBaseModel):
    all_invites_processed_successfully: bool
    sms_failures_count: int = 0
    sms_phone_number_failures: list[str] = Field(default_factory=list)


class Invitation(SQLModel, table=True):
    __tablename__ = "invitations"

    id: uuid.UUID = Field(
        default=None,
        primary_key=True,
        index=True,
        nullable=False,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    trip_id: uuid.UUID = Field(foreign_key="trips.id", nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    claim_user_id: uuid.UUID = Field(nullable=True)
    rsvp: str | None = Field(
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


class InvitationRsvp(ConfiguredBaseModel):
    rsvp: str | None = None
    paid: int | None = None
