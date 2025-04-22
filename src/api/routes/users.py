"""FastAPI endpoints for querying and retrieving user data."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import select

from core.exceptions import ResourceNotFoundError
from models.shared import DTO
from models.user import User, UserPublic
from src.api.deps import SessionDep, get_current_user

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
