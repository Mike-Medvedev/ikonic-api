"""Data Models for Invite Entities.

Defines the database tables and relationships for inviting and Rsvping to trips.
"""

import uuid

from models.user import User

from .model_config import ConfiguredBaseModel


class DeepLink(ConfiguredBaseModel):
    deep_link: str


class InviteCreate(ConfiguredBaseModel):
    user_id: uuid.UUID


class AttendanceList(ConfiguredBaseModel):
    accepted: list[User]
    pending: list[User]
    uncertain: list[User]
    declined: list[User]
