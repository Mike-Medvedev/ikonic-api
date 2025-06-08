"""FastAPI endpoints for retrieving and querying trip invite data."""

import logging
import urllib
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from core.exceptions import InvalidTokenError, ResourceNotFoundError
from models.models import (
    AttendanceList,
    ExternalInvitee,
    Invitation,
    InvitationBatchResponseData,
    InvitationCreate,
    InvitationEnum,
    InvitationUpdate,
    RegisteredInvitee,
    Trip,
    User,
)
from models.shared import DTO
from src.api.deps import (
    SecurityDep,
    SessionDep,
    VonageDep,
    get_current_user,
    send_sms_invte,
)
from src.core.config import settings

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
    sorted_users = {"accepted": [], "pending": [], "uncertain": [], "declined": []}

    for user, rsvp in users:
        if not rsvp:
            continue
        sorted_users[rsvp].append(user)
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
            except Exception:
                phone_numbers_that_failed.append(user.phone)
                logger.exception(
                    f"Failed to send SMS to user {user.id} at phone {user.phone}"  # noqa: G004
                )
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
            except Exception:
                phone_numbers_that_failed.append(invite.phone_number)
                logger.exception(
                    f"Failed to send SMS to user {user.id} at phone {user.phone}"  # noqa: G004
                )
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


# TODO: fix phone number comparison and fix in UI phone number validation input
@router.patch(
    "/invites",
    response_model=DTO[bool],
    dependencies=[Depends(get_current_user)],
)
def rsvp(
    trip_id: str,
    user: SecurityDep,
    invitation_update: InvitationUpdate,
    session: SessionDep,
) -> dict:
    """RSVP to a trip invite."""
    if not invitation_update.invite_token:
        raise InvalidTokenError("Token", invitation_update.invite_token)
    current_user = session.get(User, user.id)
    trip = session.get(Trip, trip_id)
    invitation = session.get(Invitation, invitation_update.invite_token)

    if not current_user:
        raise ResourceNotFoundError("User", user.id)
    if not trip:
        raise ResourceNotFoundError("Trip", trip_id)
    if not invitation:
        raise ResourceNotFoundError("Invitation", invitation_update.invite_token)
    if not invitation_update.rsvp:
        raise HTTPException(403, "Missing RSVP update")

    if invitation.rsvp is not InvitationEnum.PENDING or invitation.claim_user_id:
        raise HTTPException(409, "Invitation has already been RSVP'd")

    if invitation.registered_phone and user.phone != invitation.registered_phone:
        logger.info(invitation.registered_phone)
        logger.info(user.phone)
        raise HTTPException(403, "User is not the intended external invitee")

    if invitation.user_id and current_user.id != invitation.user_id:
        raise HTTPException(403, "User is not the intended registered invitee")

    invitation.sqlmodel_update(invitation_update.model_dump(exclude={"invite_token"}))
    invitation.claim_user_id = user.id
    invitation.user_id = user.id
    session.add(invitation)
    session.commit()

    return {"data": True}


def generate_invite_link(trip_id: UUID, invitation_id: UUID) -> str:
    """Use urllib to create a deeplink with trip id and invite token for trip rsvp."""
    scheme = settings.FRONTEND_SCHEME
    netloc = settings.NETLOC
    path = f"/--/trips/{trip_id}/rsvp"
    query_params = {
        "invite_token": invitation_id,
    }
    query_string = urllib.parse.urlencode(query_params)
    fragment = ""
    return urllib.parse.urlunsplit((scheme, netloc, path, query_string, fragment))
