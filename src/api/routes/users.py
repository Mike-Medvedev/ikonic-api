"""FastAPI endpoints for querying and retrieving user data."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import and_, select

from src.api.deps import SecurityDep, SessionDep, get_current_user
from src.core.exceptions import ResourceNotFoundError
from src.models.models import (
    Invitation,
    InvitationEnum,
    InvitationPublic,
    Trip,
    User,
    UserPublic,
    UserUpdate,
)
from src.models.shared import DTO

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
    """Mark the currently authenticated user as having completed onboarding and backfill user_id's to any pending invitations of the new user."""
    user_db = session.get(User, user.id)
    if not user_db:
        raise ResourceNotFoundError("User", user.id)

    user_db.is_onboarded = True
    session.add(user_db)

    # Backfill user_id for any invitations sent to this user's phone number
    if user_db.phone:
        invitations_to_update = session.exec(
            select(Invitation).where(
                and_(
                    Invitation.registered_phone == user_db.phone,
                    Invitation.user_id.is_(None),
                )
            )
        ).all()

        for invitation in invitations_to_update:
            invitation.user_id = user.id
            session.add(invitation)

    session.commit()
    return {"data": True}


@router.get(
    "/{user_id}/invites",
    dependencies=[Depends(get_current_user)],
    response_model=DTO[list[InvitationPublic]],
)
def get_invitations(
    user_id: UUID,
    session: SessionDep,
) -> dict:
    """Return incoming or outgoing invitations for a given user."""
    user = session.get(User, user_id)
    if not user:
        logger.exception(
            "Error User Not found with id %(user_id)s", {"user_id": user_id}
        )
        raise ResourceNotFoundError("User", user_id)
    statement = (
        select(Invitation, Trip, User.firstname, User.lastname)
        .join(Trip, Invitation.trip_id == Trip.id)
        .join(User, Trip.owner == User.id)
        .where(
            and_(
                Invitation.user_id == user_id, Invitation.rsvp == InvitationEnum.PENDING
            )
        )
    )

    results = session.exec(statement).all()

    invitations = []
    for invitation, trip, owner_firstname, owner_lastname in results:
        invitation_public = InvitationPublic(
            id=invitation.id,
            trip_id=invitation.trip_id,
            trip_owner=f"{owner_firstname} {owner_lastname}",
            trip_title=trip.title,
            rsvp=invitation.rsvp,
            recipient_id=invitation.user_id,
            created_at=invitation.created_at,
        )
        invitations.append(invitation_public)
    return {"data": invitations}
