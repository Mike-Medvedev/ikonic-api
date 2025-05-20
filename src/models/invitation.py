"""Data Models for Invite Entities.

Defines the database tables and relationships for inviting and Rsvping to trips.
"""

import uuid
from enum import Enum
from typing import Literal

from sqlalchemy import Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlmodel import Field, SQLModel

from models.user import UserPublic

from .model_config import ConfiguredBaseModel


class RegisteredInvitee(ConfiguredBaseModel):
    type: Literal["registered"] = "registered"
    user_id: uuid.UUID = Field(alias="userId")


class ExternalInvitee(ConfiguredBaseModel):
    type: Literal["external"] = "external"
    phone_number: str = Field(alias="phoneNumber")


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
    __table_args__ = {"schema": "public"}

    id: uuid.UUID = Field(
        default=None,
        primary_key=True,
        index=True,
        nullable=False,
    )
    trip_id: uuid.UUID = Field(
        foreign_key="public.trips.id", nullable=False, ondelete="CASCADE"
    )
    user_id: uuid.UUID = Field(
        foreign_key="public.users.id", default=None, nullable=True, ondelete="CASCADE"
    )
    claim_user_id: uuid.UUID = Field(default=None, nullable=True)
    registered_phone: str = Field(default=None, max_length=10, nullable=True)
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
