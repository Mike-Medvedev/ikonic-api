"""FastAPI endpoints for retrieving and querying trip invite data."""

import logging
import urllib
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from vonage_sms.errors import SmsError as VonageSmsError

from core.exceptions import ResourceNotFoundError
from models.invitation import (
    AttendanceList,
    ExternalInvitee,
    Invitation,
    InvitationBatchResponseData,
    InvitationCreate,
    InvitationRsvp,
    RegisteredInvitee,
)
from models.shared import DTO
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
        select(User, Invitation.rsvp)
        .join(Invitation, Invitation.user_id == User.id)
        .where(Invitation.trip_id == trip_id)
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
    response_model=DTO[InvitationBatchResponseData],
    dependencies=[Depends(get_current_user)],
)
def invite_users(  # noqa: PLR0912
    trip_id: uuid.UUID,
    payload: InvitationCreate,
    session: SessionDep,
    vonage: VonageDep,
) -> dict:
    """Invited users are classified as registered or external users.

    Registered Users have a user Id which is their source of authenticity
    External Users use their phone number

    SMS errors are just skipped and logged
    """
    if not payload.invitees:
        raise HTTPException(
            status_code=400, detail="Please provide at least one user to invite."
        )
    invitations_to_create = []
    phone_numbers_that_failed = []
    for invite in payload.invitees:
        if isinstance(invite, RegisteredInvitee):
            user = session.get(User, invite.user_id)
            existing_invitation_statement = select(Invitation).where(
                Invitation.trip_id == trip_id,
                Invitation.user_id == invite.user_id,
            )
            existing_invitation = session.exec(existing_invitation_statement).first()
            if not user:
                logger.error("Inviting Registered users account not found")
                phone_numbers_that_failed.append("User_ID_%s}_NoPhone", invite.user_id)
                continue
            if existing_invitation:
                logger.warning(
                    "Invitation Already Exists with Status: %s and User id %s",
                    existing_invitation.rsvp,
                    user.id,
                )
                continue
            if not user.phone:
                logger.warning("User %s has no phone number. Skipping SMS.", user.id)
                phone_numbers_that_failed.append("User_ID_%s}_NoPhone", user.id)
                continue
            invitation_id = uuid.uuid4()
            try:
                deep_link = generate_invite_link(
                    trip_id=trip_id, invitation_id=invitation_id
                )
                send_sms_invte(user.phone, deep_link, vonage)
            except VonageSmsError:
                phone_numbers_that_failed.append(user.phone)
            else:
                # add invited users to trips in 'pending' state
                invitations_to_create.append(
                    Invitation(
                        id=invitation_id, trip_id=trip_id, user_id=invite.user_id
                    )
                )
        elif isinstance(invite, ExternalInvitee):
            if not invite.phone_number:
                logger.warning("External User does not have a phone number")
                continue
            invitation_id = uuid.uuid4()
            try:
                deep_link = generate_invite_link(
                    trip_id=trip_id, invitation_id=invitation_id
                )
                send_sms_invte(invite.phone_number, deep_link, vonage)
            except VonageSmsError:
                phone_numbers_that_failed.append(invite.phone_number)
            else:
                invitations_to_create.append(
                    Invitation(
                        id=invitation_id,
                        trip_id=trip_id,
                        registered_phone=invite.phone_number,
                    )
                )

    if invitations_to_create:
        session.add_all(invitations_to_create)
        session.commit()
    if len(phone_numbers_that_failed) > 0:
        return {
            "data": InvitationBatchResponseData(
                all_invites_processed_successfully=False,
                sms_failures_count=len(phone_numbers_that_failed),
                sms_phone_number_failures=phone_numbers_that_failed,
            )
        }
    return {
        "data": InvitationBatchResponseData(
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
def rsvp(trip_id: str, user_id: UUID, res: InvitationRsvp, session: SessionDep) -> dict:
    """RSVP to a trip invite."""
    invitation = session.get(Invitation, (trip_id, user_id))
    resource = "invitation"
    if not invitation:
        raise ResourceNotFoundError(resource, f"{trip_id}: {user_id}")
    rsvp = res.model_dump(exclude_unset=True)
    updated_invitation = invitation.sqlmodel_update(rsvp)
    session.add(updated_invitation)
    session.commit()
    return {"data": True}


def generate_invite_link(trip_id: UUID, invitation_id: UUID) -> str:
    """Use urllib to create a deeplink with trip id and invite token for trip rsvp."""
    scheme = "exp"
    netloc = "192.168.1.20:8081"
    path = f"/--/trips/{trip_id}/rsvp"
    query_params = {
        "trip_id": trip_id,
        "invite_token": invitation_id,
    }
    query_string = urllib.parse.urlencode(query_params)
    fragment = ""
    return urllib.parse.urlunsplit((scheme, netloc, path, query_string, fragment))
