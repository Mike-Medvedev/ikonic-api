"""FastAPI endpoints for retrieving and querying trip invite data."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import select
from vonage_sms.errors import SmsError as VonageSmsError

from core.exceptions import ResourceNotFoundError, SmsError
from models.invite import AttendanceList, DeepLink
from models.shared import DTO
from models.trip import TripParticipation, TripParticipationRsvp
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
    response_model=DTO[AttendanceList],
    dependencies=[Depends(get_current_user)],
)
def get_invited_users(trip_id: int, session: SessionDep) -> dict:
    """Return Invited Users for a trip."""
    statement = (
        select(User, TripParticipation.rsvp)
        .join(TripParticipation, TripParticipation.user_id == User.id)
        .where(TripParticipation.trip_id == trip_id)
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
    response_model=DTO[bool],
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
    resource = "User"
    if not user:
        raise ResourceNotFoundError(resource, user_id)
    try:
        send_sms_invte(user.phone, deep_link.deep_link, vonage)
    except VonageSmsError as exc:
        resource = "SMS"
        raise SmsError(resource, user_id) from exc

    # add user to trip in 'pending' state
    record = TripParticipation(trip_id=trip_id, user_id=user_id)
    session.add(record)
    session.commit()

    return {"data": True}


@router.patch(
    "/invites/{user_id}",
    response_model=DTO[bool],
    dependencies=[Depends(get_current_user)],
)
def rsvp(
    trip_id: int, user_id: UUID, res: TripParticipationRsvp, session: SessionDep
) -> dict:
    """RSVP to a trip invite."""
    participation = session.get(TripParticipation, (trip_id, user_id))
    resource = "participation"
    if not participation:
        raise ResourceNotFoundError(resource, f"{trip_id}: {user_id}")
    rsvp = res.model_dump(exclude_unset=True)
    updated_participation = participation.sqlmodel_update(rsvp)
    session.add(updated_participation)
    session.commit()
    return {"data": True}
