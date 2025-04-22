"""FastAPI endpoints for querying and retrieving trips data."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import selectinload
from sqlmodel import select

from core.exceptions import ResourceNotFoundError
from models.shared import DTO
from models.trip import Trip, TripCreate, TripPublic, TripUpdate, TripUserLink
from models.user import User
from src.api.deps import (
    SecurityDep,
    SessionDep,
    get_current_user,
)

router = APIRouter(prefix="/trips", tags=["trips"])

logger = logging.getLogger(__name__)


@router.get("/", response_model=DTO[list[TripPublic]])
def get_trips(session: SessionDep, user: SecurityDep) -> dict:
    """Return all trips for a user."""
    query = (
        select(Trip)
        .join(TripUserLink, Trip.id == TripUserLink.trip_id)
        .options(selectinload(Trip.owner_user))
        .where(TripUserLink.user_id == user.id)
    )
    trips = session.exec(query).all()
    trips_public = [
        TripPublic(
            **trip.model_dump(exclude={"owner"}),
            owner=trip.owner_user.model_dump(),
        )
        for trip in trips
    ]

    return {"data": trips_public}


@router.get(
    "/{trip_id}",
    response_model=DTO[TripPublic],
    dependencies=[Depends(get_current_user)],
)
async def get_trip(trip_id: int, session: SessionDep) -> dict:
    """Return a specific trip for a user."""
    query = (
        select(Trip).options(selectinload(Trip.owner_user)).where(Trip.id == trip_id)
    )
    trip = session.exec(query).one_or_none()

    resource = "Trip"
    if not trip:
        raise ResourceNotFoundError(resource, trip_id)

    trip_public = TripPublic(
        **trip.model_dump(exclude={"owner"}), owner=trip.owner_user.model_dump()
    )
    return {"data": trip_public}


@router.post("/", response_model=DTO[TripPublic])
async def create_trip(trip: TripCreate, user: SecurityDep, session: SessionDep) -> dict:
    """Create a new trip and link new trip to user."""
    owner = user.id
    new_trip = Trip(**trip.model_dump(), owner=owner)
    session.add(new_trip)
    session.flush()
    # TODO: Rework TripUserLink model into UserTrip Map and fix naming
    link = TripUserLink(
        trip_id=new_trip.id,
        # map new trip to owner and init rsvp to "accepted"
        user_id=user.id,
        rsvp="accepted",
    )
    session.add(link)
    session.commit()
    session.refresh(new_trip)
    owner = session.get(User, user.id)
    session.refresh(new_trip)
    return {"data": TripPublic(**new_trip.model_dump(exclude={"owner"}), owner=owner)}


@router.patch(
    "/{trip_id}",
    response_model=DTO[TripPublic],
    dependencies=[Depends(get_current_user)],
)
async def update_trip(trip: TripUpdate, trip_id: int, session: SessionDep) -> dict:
    """Update existing trip data and refetch updated trip with owner."""
    trip_db = session.get(Trip, trip_id)
    resource = "Trip"
    if not trip_db:
        raise ResourceNotFoundError(resource, trip_id)

    trip_update_data = trip.model_dump(exclude_unset=True)
    trip_db.sqlmodel_update(trip_update_data)
    session.add(trip_db)
    session.commit()
    session.refresh(trip_db)

    # Re-query with eager loading to get the owner_user relationship.
    query = (
        select(Trip).where(Trip.id == trip_id).options(selectinload(Trip.owner_user))
    )
    updated_trip = session.exec(query).one_or_none()
    if not updated_trip:
        raise ResourceNotFoundError(resource, trip_id)

    response_trip = TripPublic(
        **updated_trip.model_dump(exclude={"owner"}), owner=updated_trip.owner_user
    )
    return {"data": response_trip}


@router.delete("/{trip_id}", dependencies=[Depends(get_current_user)])
def delete_trip(trip_id: int, session: SessionDep) -> dict:
    """Delete the specified trip."""
    trip_db = session.get(Trip, trip_id)
    resource = "Trip"
    if not trip_db:
        raise ResourceNotFoundError(resource, trip_id)
    session.delete(trip_db)
    session.commit()
    return {"data": True}
