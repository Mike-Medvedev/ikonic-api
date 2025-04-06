from typing import List
import uuid
from fastapi import APIRouter, HTTPException
from src.api.deps import SessionDep
from src.models import Trip, TripCreate, TripUpdate, TripUserLink, TripPublic, DTO, Car, CarCreate, CarPublic
from sqlmodel import select

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post('/', response_model=DTO[TripPublic])
async def create_trip(trip: TripCreate, session: SessionDep):
    hardcoded_user = uuid.UUID("e25b2f98-f6e0-4a54-84f6-16f42cb849b4")
    valid_trip = Trip.model_validate(trip)
    session.add(valid_trip)
    session.flush()
    link = TripUserLink(trip_id=valid_trip.id, user_id=hardcoded_user)
    session.add(link)
    session.commit()
    return {"data": valid_trip}


@router.get('/', response_model=DTO[List[TripPublic]])
def get_trips(session: SessionDep):
    user_id = "e25b2f98-f6e0-4a54-84f6-16f42cb849b4"
    query = select(Trip).join(TripUserLink, Trip.id == TripUserLink.trip_id).where(
        TripUserLink.user_id == user_id)
    trips = session.exec(query).all()
    return {"data": trips}


@router.get('/{id}', response_model=DTO[TripPublic])
async def get_trip(id: int, session: SessionDep):
    trip = session.get(Trip, id)
    return {"data": trip}


@router.patch('/{id}', response_model=DTO[TripPublic])
async def update_trip(trip: TripUpdate, id: int, session: SessionDep):
    trip_db = session.get(Trip, id)
    if not id:
        raise HTTPException(
            status_code=404, detail="Error Trip To Update Not Found")
    trip_update_data = trip.model_dump(exclude_unset=True)
    trip_db.sqlmodel_update(trip_update_data)
    session.add(trip_db)
    session.commit()
    session.refresh(trip_db)
    return {"data": trip_db}


@router.delete('/{id}')
def delete_post(id: int, session: SessionDep):
    trip_db = session.get(Trip, id)
    if not trip_db:
        raise HTTPException(status_code=404, detail="Trip Not Found")
    session.delete(trip_db)
    session.commit()
    return {"data": True}


@router.get('/{id}/cars', response_model=DTO[List[Car]])
def get_cars_for_trip(id: int, session: SessionDep):
    cars = session.exec(select(Car).join(Trip).where(Trip.id == id)).all()
    return {"data": list(cars)}


@router.post('/{id}/cars', response_model=DTO[CarPublic])
def create_car(id: int, car: CarCreate, session: SessionDep):
    new_car = Car(**car.model_dump(), trip_id=id)
    session.add(new_car)
    session.commit()
    session.refresh(new_car)
    return {"data": new_car}


@router.get('/{trip_id}/cars/{car_id}')
def get_car_by_id(trip_id: int, car_id: int, session: SessionDep):
    car = session.exec(select(Car).where(
        Car.trip_id == trip_id, Car.id == car_id)).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car Not Found")
    return {"data": car}


@router.delete('/{trip_id}/cars/{car_id}')
def delete_car(trip_id: int, car_id: int, session: SessionDep):
    query = select(Car).where(Car.trip_id == trip_id, Car.id == car_id)
    car = session.exec(query).first()
    if not car:
        raise HTTPException(status_code=404, detail="Error Car Not Found")
    session.delete(car)
    session.commit()
    return {"data": True}
