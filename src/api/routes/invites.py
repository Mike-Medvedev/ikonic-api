"""FastAPI endpoints for retrieving and querying trip invite data."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from models.invite import DeepLink, SortedUsersResponse
from models.shared import DTO
from models.trip import TripUserLink, TripUserLinkRsvp
from models.user import User
from src.api.deps import (
    SessionDep,
    VonageDep,
    get_current_user,
    send_sms_invte,
)

router = APIRouter(prefix="/trips/{trip_id}", tags=["invites"])

logger = logging.getLogger(__name__)


@router.get(
    "/invites",
    response_model=DTO[SortedUsersResponse],
    dependencies=[Depends(get_current_user)],
)
def get_invited_users(trip_id: int, session: SessionDep) -> dict:
    """Return Invited Users for a trip."""
    statement = (
        select(User, TripUserLink.rsvp)
        .join(TripUserLink, TripUserLink.user_id == User.id)
        .where(TripUserLink.trip_id == trip_id)
    )
    users = session.exec(statement).all()
    logger.info(users)
    sorted_users = {"accepted": [], "pending": [], "uncertain": [], "declined": []}

    for user, rsvp in users:
        if not rsvp:
            continue
        sorted_users[rsvp].append(user)
    logger.info(sorted_users)
    return {"data": sorted_users}


@router.post(
    "/invites/{user_id}",
    response_model=DTO[TripUserLink],
    status_code=201,
    dependencies=[Depends(get_current_user)],
)
def invite_user(
    trip_id: int,
    user_id: UUID,
    deep_link: DeepLink,
    session: SessionDep,
    vonage: VonageDep,
) -> dict:
    """Invite a user to a trip."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    response = send_sms_invte(user.phone, deep_link.deep_link, vonage)
    if not response:
        raise HTTPException(status_code=400, detail="Error Sending SMS")
    link = TripUserLink(trip_id=trip_id, user_id=user_id)
    return {"data": link}


@router.patch(
    "/invites/{user_id}",
    response_model=DTO[TripUserLink],
    dependencies=[Depends(get_current_user)],
)
def rsvp(
    trip_id: int, user_id: UUID, res: TripUserLinkRsvp, session: SessionDep
) -> dict:
    """RSVP to a trip invite."""
    link = session.get(TripUserLink, (trip_id, user_id))
    if not link:
        raise HTTPException(status_code=404, detail="Link Not Found")
    rsvp = res.model_dump(exclude_unset=True)
    updated_link = link.sqlmodel_update(rsvp)
    session.add(updated_link)
    session.commit()
    session.refresh(updated_link)
    return {"data": updated_link}
