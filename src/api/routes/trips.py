import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select

logger = logging.getLogger(__name__)

from src.api.deps import (
    SecurityDep,
    SessionDep,
    VonageDep,
    send_sms_invte,
)
from src.models import (
    DTO,
    Car,
    CarCreate,
    CarPublic,
    DeepLink,
    Passenger,
    PassengerCreate,
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
    dependencies=[SecurityDep],
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


@router.patch(
    "/{trip_id}",
    response_model=DTO[TripPublic],
    dependencies=[SecurityDep],
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


@router.delete("/{trip_id}", dependencies=[SecurityDep])
def delete_trip(trip_id: int, session: SessionDep):
    trip_db = session.get(Trip, trip_id)
    if not trip_db:
        raise HTTPException(status_code=404, detail="Trip Not Found")
    session.delete(trip_db)
    session.commit()
    return {"data": True}


@router.get(
    "/{trip_id}/cars",
    response_model=DTO[list[CarPublic]],
    dependencies=[SecurityDep],
)
def get_cars_for_trip(trip_id: int, session: SessionDep):
    cars = session.exec(
        select(Car).where(Car.trip_id == trip_id).options(selectinload(Car.owner_user))
    ).all()

    cars_public = [
        CarPublic(**car.model_dump(exclude={"owner"}), owner=car.owner_user)
        for car in cars
    ]

    return {"data": cars_public}


@router.post("/{trip_id}/cars", response_model=DTO[CarPublic])
def create_car(trip_id: int, car: CarCreate, session: SessionDep, user: SecurityDep):
    new_car = Car(**car.model_dump(), trip_id=trip_id, owner=user.id)
    session.add(new_car)
    session.commit()
    # Refresh to load both the new Car's data and its owner relationship.
    session.refresh(new_car, attribute_names=["owner_user"])

    # Build and return the CarPublic representation.
    car_public = CarPublic(
        **new_car.model_dump(exclude={"owner"}), owner=new_car.owner_user
    )
    return {"data": car_public}


@router.get("/{trip_id}/cars/{car_id}", dependencies=[SecurityDep])
def get_car_by_id(trip_id: int, car_id: int, session: SessionDep):
    car = session.exec(
        select(Car).where(Car.trip_id == trip_id, Car.id == car_id)
    ).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car Not Found")
    return {"data": car}


@router.delete("/{trip_id}/cars/{car_id}", dependencies=[SecurityDep])
def delete_car(trip_id: int, car_id: int, session: SessionDep):
    query = select(Car).where(Car.trip_id == trip_id, Car.id == car_id)
    car = session.exec(query).first()
    if not car:
        raise HTTPException(status_code=404, detail="Error Car Not Found")
    session.delete(car)
    session.commit()
    return {"data": True}


@router.get(
    "/{trip_id}/invites",
    response_model=DTO[SortedUsersResponse],
    dependencies=[SecurityDep],
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
    dependencies=[Depends(SecurityDep)],
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
    dependencies=[Depends(SecurityDep)],
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


@router.post(
    "/{trip_id}/cars/{car_id}/passengers",
    response_model=DTO[PassengerCreate],
    dependencies=[SecurityDep],
)
def add_passenger(
    trip_id: int,
    car_id: int,
    user: SecurityDep,
    passenger: PassengerCreate,
    session: SessionDep,
):
    car = session.get(Car, car_id)
    if not car or car.trip_id != trip_id:
        raise HTTPException(404, "Car not found on this trip")

    user = session.get(User, user.id)
    if not user:
        raise HTTPException(404, "User not found")
    new_passenger = Passenger(**passenger.model_dump(), user_id=user.id, car_id=car_id)
    session.add(new_passenger)
    session.commit()
    session.refresh(new_passenger)
    logger.info(car.passengers)
    return {"data": new_passenger}


@router.get("/{trip_id}/cars/{car_id}/passengers", response_model=DTO[list[Passenger]])
def get_passengers(trip_id: int, car_id: int, session: SessionDep):
    car = session.get(Car, car_id)
    if not car or car.trip_id != trip_id:
        raise HTTPException(404, "Car not found on this trip")
    session.refresh(car)
    logger.info("printing car %s", car)
    return {"data": car.passengers}
