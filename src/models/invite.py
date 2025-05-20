"""Data Models for Invite Entities.

Defines the database tables and relationships for inviting and Rsvping to trips.
"""

from pydantic import Field

from models.trip import TripParticipationCreate
from models.user import UserPublic

from .model_config import ConfiguredBaseModel


class InviteCreate(ConfiguredBaseModel):
    invites: list[TripParticipationCreate]
    deep_link: str = Field(alias="deepLink")


class AttendanceList(ConfiguredBaseModel):
    accepted: list[UserPublic]
    pending: list[UserPublic]
    uncertain: list[UserPublic]
    declined: list[UserPublic]


class InviteBatchResponseData(ConfiguredBaseModel):
    all_invites_processed_successfully: bool
    sms_failures_count: int = 0
    sms_phone_number_failures: list[str] = Field(default_factory=list)
