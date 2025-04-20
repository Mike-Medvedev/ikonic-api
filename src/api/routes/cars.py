"""FastAPI endpoints for retrieving and querying car data."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select

from api.deps import SecurityDep, SessionDep, get_current_user
from models.car import Car, CarCreate, CarPublic, Passenger, PassengerCreate
from models.shared import DTO
from models.user import User

router = APIRouter(prefix="/trips/{trip_id}/cars", tags=["cars"])

logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=DTO[list[CarPublic]],
    dependencies=[Depends(get_current_user)],
)
def get_cars_for_trip(trip_id: int, session: SessionDep) -> dict:
    """Return all cars for a trip."""
    cars = session.exec(
        select(Car).where(Car.trip_id == trip_id).options(selectinload(Car.owner_user))
    ).all()

    cars_public = [
        CarPublic(**car.model_dump(exclude={"owner"}), owner=car.owner_user)
        for car in cars
    ]

    return {"data": cars_public}


@router.get("/{car_id}", dependencies=[Depends(get_current_user)])
def get_car_by_id(trip_id: int, car_id: int, session: SessionDep) -> dict:
    """Return a car."""
    car = session.exec(
        select(Car).where(Car.trip_id == trip_id, Car.id == car_id)
    ).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car Not Found")
    return {"data": car}


@router.post("/", response_model=DTO[CarPublic])
def create_car(
    trip_id: int, car: CarCreate, session: SessionDep, user: SecurityDep
) -> dict:
    """Create a new car."""
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


@router.delete("/{car_id}", dependencies=[Depends(get_current_user)])
def delete_car(trip_id: int, car_id: int, session: SessionDep) -> dict:
    """Delete a car."""
    query = select(Car).where(Car.trip_id == trip_id, Car.id == car_id)
    car = session.exec(query).first()
    if not car:
        raise HTTPException(status_code=404, detail="Error Car Not Found")
    session.delete(car)
    session.commit()
    return {"data": True}


@router.post(
    "/{car_id}/passengers",
    response_model=DTO[PassengerCreate],
    dependencies=[Depends(get_current_user)],
)
def add_passenger(
    trip_id: int,
    car_id: int,
    user: SecurityDep,
    passenger: PassengerCreate,
    session: SessionDep,
) -> dict:
    """Add a passenger to a car."""
    car = session.get(Car, car_id)
    if not car or car.trip_id != trip_id:
        raise HTTPException(404, "Car not found on this trip")

    user = session.get(User, user.id)
    if not user:
        raise HTTPException(404, "User not found")
    # TODO: fix logic and decide whether to have role based passenger selection
    new_passenger = Passenger(**passenger.model_dump(), user_id=user.id, car_id=car_id)
    session.add(new_passenger)
    session.commit()
    session.refresh(new_passenger)
    return {"data": new_passenger}


@router.get(
    "/{car_id}/passengers",
    response_model=DTO[list[Passenger]],
    dependencies=[Depends(get_current_user)],
)
def get_passengers(trip_id: int, car_id: int, session: SessionDep) -> dict:
    """Return all passengers for a car."""
    car = session.get(Car, car_id)
    if not car or car.trip_id != trip_id:
        raise HTTPException(404, "Car not found on this trip")
    session.refresh(car)
    return {"data": car.passengers}
