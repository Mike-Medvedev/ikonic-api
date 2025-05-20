"""FastAPI endpoints for retrieving and querying trip invite data."""

import logging
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from vonage_sms.errors import SmsError as VonageSmsError

from core.exceptions import ResourceNotFoundError
from models.invite import AttendanceList, InviteBatchResponseData, InviteCreate
from models.shared import DTO
from models.trip import (
    TripParticipation,
    TripParticipationRsvp,
)
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
def get_invited_users(trip_id: str, session: SessionDep) -> dict:
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
    "/invites",
    response_model=DTO[InviteBatchResponseData],
    dependencies=[Depends(get_current_user)],
)
def invite_users(
    trip_id: uuid.UUID,
    payload: InviteCreate,
    session: SessionDep,
    vonage: VonageDep,
) -> dict:
    """Invite users to a trip."""
    invites = payload.invites
    deep_link = payload.deep_link
    if not invites:
        raise HTTPException(
            status_code=400, detail="Please provide at least one user to invite."
        )
    records = []
    phone_numbers_that_failed = []
    for invite in invites:
        user = session.get(User, invite.user_id)
        participant = session.get(TripParticipation, (trip_id, invite.user_id))
        if not user:
            logger.warning("Inviting User who does not have an account yet")
            continue
        if participant:
            logger.warning("User with id %s is already invited", user.id)
            continue
        if not user.phone:
            logger.warning("User %s has no phone number. Skipping SMS.", user.id)
            phone_numbers_that_failed.append("User_ID_%s}_NoPhone", user.id)
            continue
        try:
            send_sms_invte(user.phone, deep_link, vonage)
        except VonageSmsError:
            phone_numbers_that_failed.append(user.phone)
        else:
            # add invited users to trips in 'pending' state
            records.append(TripParticipation(trip_id=trip_id, **invite.model_dump()))
    if records:
        session.add_all(records)
        session.commit()
    if len(phone_numbers_that_failed) > 0:
        return {
            "data": InviteBatchResponseData(
                all_invites_processed_successfully=False,
                sms_failures_count=len(phone_numbers_that_failed),
                sms_phone_number_failures=phone_numbers_that_failed,
            )
        }
    return {
        "data": InviteBatchResponseData(
            all_invites_processed_successfully=True,
            sms_failures_count=0,
            sms_phone_number_failures=[],
        )
    }


@router.patch(
    "/invites/{user_id}",
    response_model=DTO[bool],
    dependencies=[Depends(get_current_user)],
)
def rsvp(
    trip_id: str, user_id: UUID, res: TripParticipationRsvp, session: SessionDep
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
