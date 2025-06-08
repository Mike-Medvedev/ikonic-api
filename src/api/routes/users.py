"""FastAPI endpoints for querying and retrieving user data."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import select

from core.exceptions import ResourceNotFoundError
from models.models import (
    User,
    UserPublic,
    UserUpdate,
)
from models.shared import DTO
from src.api.deps import SecurityDep, SessionDep, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

logger = logging.getLogger(__name__)


@router.get(
    "/", response_model=DTO[list[UserPublic]], dependencies=[Depends(get_current_user)]
)
def get_users(session: SessionDep) -> dict:
    """Return every user in the database."""
    users = session.exec(select(User)).all()
    logger.info("Fetching Users %s", users)
    return {"data": list(users)}


@router.get(
    "/{user_id}",
    dependencies=[Depends(get_current_user)],
    response_model=DTO[UserPublic],
)
def get_user_by_id(user_id: UUID, session: SessionDep) -> dict:
    """Return a specified user."""
    user = session.get(User, user_id)
    resource_type = "User"
    if not user:
        raise ResourceNotFoundError(resource_type, user_id)
    logger.info("Successfully fetched user %s by ID: %s", user, user_id)
    return {"data": user}


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_user)],
    response_model=DTO[UserPublic],
)
def update_user(user_id: UUID, user: UserUpdate, session: SessionDep) -> dict:
    """Update a user."""
    user_db = session.get(User, user_id)
    if not user_db:
        raise ResourceNotFoundError("User", user_id)
    updated_user = user.model_dump(exclude_unset=True)
    user_db.sqlmodel_update(updated_user)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return {"data": user_db}


@router.post(
    "/onboarding",
    response_model=DTO[bool],
)
def complete_onboarding(user: SecurityDep, session: SessionDep) -> dict:
    """Mark the currently authenticated user as having completed onboarding."""
    user_db = session.get(User, user.id)
    if not user_db:
        raise ResourceNotFoundError("User", user.id)
    user_db.is_onboarded = True
    session.add(user_db)
    session.commit()
    return {"data": True}
