import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select

logger = logging.getLogger(__name__)

from src.api.deps import (
    SecurityDep,
    SessionDep,
    VonageDep,
    get_current_user,
    send_sms_invte,
)
from src.models import (
    DTO,
    DeepLink,
    SortedUsersResponse,
    Trip,
    TripCreate,
    TripPublic,
    TripUpdate,
    TripUserLink,
    TripUserLinkRsvp,
    User,
)

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("", response_model=DTO[list[TripPublic]])
def get_trips(session: SessionDep, user: SecurityDep):
    query = (
        select(Trip)
        .join(TripUserLink, Trip.id == TripUserLink.trip_id)
        .options(selectinload(Trip.owner_user))
        .where(TripUserLink.user_id == user.id)
    )
    trips = session.exec(query).all()

    trips_public = [
        TripPublic(**trip.model_dump(exclude={"owner"}), owner=trip.owner_user)
        for trip in trips
    ]

    return {"data": trips_public}


@router.get(
    "/{trip_id}",
    response_model=DTO[TripPublic],
    dependencies=[Depends(get_current_user)],
)
async def get_trip(trip_id: int, session: SessionDep):
    query = (
        select(Trip).options(selectinload(Trip.owner_user)).where(Trip.id == trip_id)
    )
    trip = session.exec(query).one_or_none()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip_public = TripPublic(
        **trip.model_dump(exclude={"owner"}), owner=trip.owner_user
    )
    return {"data": trip_public}


@router.post("", response_model=DTO[TripPublic])
async def create_trip(trip: TripCreate, user: SecurityDep, session: SessionDep):
    valid_trip = Trip.model_validate(trip)
    session.add(valid_trip)
    session.flush()
    link = TripUserLink(
        trip_id=valid_trip.id,
        # map new trip to owner and init rsvp to "accepted"
        user_id=user.id,
        rsvp="accepted",
    )
    session.add(link)
    session.commit()
    owner = session.get(User, user.id)
    return {"data": TripPublic(**trip.model_dump(exclude={"owner"}), owner=owner)}


@router.patch(
    "/{trip_id}",
    response_model=DTO[TripPublic],
    dependencies=[Depends(get_current_user)],
)
async def update_trip(trip: TripUpdate, trip_id: int, session: SessionDep):
    trip_db = session.get(Trip, trip_id)
    if not trip_db:
        raise HTTPException(status_code=404, detail="Trip to update not found")

    trip_update_data = trip.model_dump(exclude_unset=True)
    trip_db.sqlmodel_update(trip_update_data)
    session.add(trip_db)
    session.commit()
    session.refresh(trip_db)

    # Re-query with eager loading to get the owner_user relationship.
    query = select(Trip).where(Trip.id == id).options(selectinload(Trip.owner_user))
    updated_trip = session.exec(query).one_or_none()
    if not updated_trip:
        raise HTTPException(status_code=404, detail="Trip not found after update")

    response_trip = TripPublic(
        **updated_trip.model_dump(exclude={"owner"}), owner=updated_trip.owner_user
    )
    return {"data": response_trip}


@router.delete("/{trip_id}", dependencies=[Depends(get_current_user)])
def delete_trip(trip_id: int, session: SessionDep):
    trip_db = session.get(Trip, trip_id)
    if not trip_db:
        raise HTTPException(status_code=404, detail="Trip Not Found")
    session.delete(trip_db)
    session.commit()
    return {"data": True}


@router.get(
    "/{trip_id}/invites",
    response_model=DTO[SortedUsersResponse],
    dependencies=[Depends(get_current_user)],
)
def get_invited_users(trip_id: int, session: SessionDep):
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
    "/{trip_id}/invites/{user_id}",
    response_model=DTO[TripUserLink],
    status_code=201,
    dependencies=[Depends(get_current_user)],
)
def invite_user(
    trip_id: int,
    user_id: str,
    deep_link: DeepLink,
    session: SessionDep,
    vonage: VonageDep,
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    response = send_sms_invte(user.phone, deep_link.deep_link, vonage)
    if not response:
        raise HTTPException(status_code=400, detail="Error Sending SMS")
    link = TripUserLink(trip_id=trip_id, user_id=user_id)
    return {"data": link}


@router.patch(
    "/{trip_id}/invites/{user_id}",
    response_model=DTO[TripUserLink],
    dependencies=[Depends(get_current_user)],
)
def create_rsvp(trip_id: int, user_id: str, res: TripUserLinkRsvp, session: SessionDep):
    link = session.get(TripUserLink, (trip_id, user_id))
    if not link:
        raise HTTPException(status_code=404, detail="Link Not Found")
    rsvp = res.model_dump(exclude_unset=True)
    updated_link = link.sqlmodel_update(rsvp)
    session.add(updated_link)
    session.commit()
    session.refresh(updated_link)
    return {"data": updated_link}
