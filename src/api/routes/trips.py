"""FastAPI endpoints for querying and retrieving trips data."""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.deps import (
    SecurityDep,
    SessionDep,
    get_current_user,
)
from src.core.exceptions import ResourceNotFoundError
from src.models.models import (
    Invitation,
    Trip,
    TripCreate,
    TripPublic,
    TripUpdate,
    User,
    UserPublic,
)
from src.models.shared import DTO

router = APIRouter(prefix="/trips", tags=["trips"])

logger = logging.getLogger(__name__)


@router.get("/", response_model=DTO[list[TripPublic]])
def get_trips(session: SessionDep, user: SecurityDep, *, past: bool = False) -> dict:
    """Return all trips for a user."""
    today_utc = datetime.now(UTC).date()

    query = (
        select(Trip)
        .join(Invitation, Trip.id == Invitation.trip_id)
        .options(selectinload(Trip.owner_user))
        .where(
            Invitation.user_id == user.id,
            Trip.end_date < today_utc if past else Trip.end_date >= today_utc,
        )
        .distinct()
    )

    trips = session.exec(query).all()
    trips_public = [
        TripPublic(
            **trip.model_dump(exclude={"owner"}),
            owner=trip.owner_user,
        )
        for trip in trips
    ]

    return {"data": trips_public}


@router.get(
    "/{trip_id}",
    response_model=DTO[TripPublic],
    dependencies=[Depends(get_current_user)],
)
async def get_trip(trip_id: str, session: SessionDep) -> dict:
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
    """Create a new trip and user as trip participant."""
    owner = user.id
    new_trip = Trip(**trip.model_dump(), owner=owner)
    logger.info("Adding new trip %s", new_trip)
    session.add(new_trip)
    session.flush()
    # associate new trip with owner
    participant = Invitation(
        id=uuid.uuid4(),
        trip_id=new_trip.id,
        user_id=user.id,
        rsvp="accepted",  # default participation to accepted
    )
    session.add(participant)
    session.commit()
    session.refresh(new_trip)
    owner = session.get(User, user.id)
    session.refresh(new_trip)
    owner_public = UserPublic.model_validate(
        owner, from_attributes=True
    )  # convert User SQLModel obj to pydantic UserPublic model
    return {
        "data": TripPublic(**new_trip.model_dump(exclude={"owner"}), owner=owner_public)
    }


@router.patch(
    "/{trip_id}",
    response_model=DTO[TripPublic],
    dependencies=[Depends(get_current_user)],
)
async def update_trip(trip: TripUpdate, trip_id: str, session: SessionDep) -> dict:
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
        **updated_trip.model_dump(exclude={"owner"}),
        owner=UserPublic.model_validate(updated_trip.owner_user),
    )
    return {"data": response_trip}


@router.delete("/{trip_id}", dependencies=[Depends(get_current_user)])
def delete_trip(trip_id: str, session: SessionDep) -> dict:
    """Delete the specified trip."""
    trip_db = session.get(Trip, trip_id)
    resource = "Trip"
    if not trip_db:
        raise ResourceNotFoundError(resource, trip_id)
    session.delete(trip_db)
    session.commit()
    return {"data": True}
