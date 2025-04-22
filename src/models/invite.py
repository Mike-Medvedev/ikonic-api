"""Data Models for Invite Entities.

Defines the database tables and relationships for inviting and Rsvping to trips.
"""

import uuid

from pydantic import BaseModel
from sqlmodel import SQLModel

from models.user import User


class DeepLink(BaseModel):
    deep_link: str


class InviteCreate(SQLModel):
    user_id: uuid.UUID


class SortedUsersResponse(BaseModel):
    accepted: list[User]
    pending: list[User]
    uncertain: list[User]
    declined: list[User]
