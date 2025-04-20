"""FastAPI endpoints for querying and retrieving user data."""

import logging

from fastapi import APIRouter, Depends
from sqlmodel import select

from src.api.deps import SessionDep, get_current_user
from src.models import DTO, User

router = APIRouter(prefix="/users", tags=["users"])

logger = logging.getLogger(__name__)


@router.get(
    "/", response_model=DTO[list[User]], dependencies=[Depends(get_current_user)]
)
def get_users(session: SessionDep) -> dict:
    """Return every user in the database."""
    users = session.exec(select(User)).all()
    logger.info("Fetching Users %s", users)
    return {"data": list(users)}


@router.get(
    "/{user_id}", dependencies=[Depends(get_current_user)], response_model=DTO[User]
)
def get_user_by_id(user_id: str, session: SessionDep) -> dict:
    """Return a specified user."""
    user = session.get(User, user_id)
    logger.info("Fetching User: %s by id: %s", user, user_id)
    return {"data": user}
