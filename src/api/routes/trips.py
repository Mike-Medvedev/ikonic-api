from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from src.api.deps import SessionDep, VonageDep, SecurityDep, get_current_user, send_sms_invte
from src.models import Trip, TripCreate, TripUpdate, TripUserLink, TripPublic, DTO, Car, CarCreate, CarPublic, TripUserLinkRsvp, Rsvp, User, Passenger, PassengerCreate
from sqlmodel import select

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post('/', response_model=DTO[TripPublic], dependencies=[Depends(get_current_user)])
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
def get_trips(session: SessionDep, user: SecurityDep):
    query = select(Trip).join(TripUserLink, Trip.id == TripUserLink.trip_id).where(
        TripUserLink.user_id == user.id)
    trips = session.exec(query).all()
    return {"data": trips}


@router.get('/{id}', response_model=DTO[TripPublic], dependencies=[Depends(get_current_user)])
async def get_trip(id: int, session: SessionDep):
    trip = session.get(Trip, id)
    return {"data": trip}


@router.patch('/{id}', response_model=DTO[TripPublic], dependencies=[Depends(get_current_user)])
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


@router.delete('/{id}', dependencies=[Depends(get_current_user)])
def delete_post(id: int, session: SessionDep):
    trip_db = session.get(Trip, id)
    if not trip_db:
        raise HTTPException(status_code=404, detail="Trip Not Found")
    session.delete(trip_db)
    session.commit()
    return {"data": True}


@router.get('/{id}/cars', response_model=DTO[List[Car]], dependencies=[Depends(get_current_user)])
def get_cars_for_trip(id: int, session: SessionDep):
    cars = session.exec(select(Car).join(Trip).where(Trip.id == id)).all()
    return {"data": list(cars)}


@router.post('/{id}/cars', response_model=DTO[CarPublic], dependencies=[Depends(get_current_user)])
def create_car(id: int, car: CarCreate, session: SessionDep):
    new_car = Car(**car.model_dump(), trip_id=id)
    session.add(new_car)
    session.commit()
    session.refresh(new_car)
    return {"data": new_car}


@router.get('/{trip_id}/cars/{car_id}', dependencies=[Depends(get_current_user)])
def get_car_by_id(trip_id: int, car_id: int, session: SessionDep):
    car = session.exec(select(Car).where(
        Car.trip_id == trip_id, Car.id == car_id)).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car Not Found")
    return {"data": car}


@router.delete('/{trip_id}/cars/{car_id}', dependencies=[Depends(get_current_user)])
def delete_car(trip_id: int, car_id: int, session: SessionDep):
    query = select(Car).where(Car.trip_id == trip_id, Car.id == car_id)
    car = session.exec(query).first()
    if not car:
        raise HTTPException(status_code=404, detail="Error Car Not Found")
    session.delete(car)
    session.commit()
    return {"data": True}


@router.get('/{trip_id}/invites', response_model=DTO[List[User]], dependencies=[Depends(get_current_user)])
def get_invited_users(trip_id: int, session: SessionDep):
    statement = (
        select(User)
        .join(TripUserLink, TripUserLink.user_id == User.id)
        .where(TripUserLink.trip_id == trip_id)
    )
    users = session.exec(statement).all()
    return {"data": users}


@router.post('/{trip_id}/invites/{user_id}', response_model=DTO[TripUserLink], status_code=201)
def invite_user(trip_id: int, user: SecurityDep, rsvp: Rsvp,  session: SessionDep, vonage: VonageDep):
    user = session.get(User, user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    response = send_sms_invte(user.phone, rsvp.deep_link, vonage)
    if not response:
        raise HTTPException(status_code=400, detail="Error Sending SMS")
    link = TripUserLink(trip_id=trip_id, user_id=uuid.UUID(user.id))
    session.add(link)
    session.commit()
    session.refresh(link)
    return {"data": link}


@router.patch('/{trip_id}/invites/{user_id}', response_model=DTO[TripUserLink])
def create_rsvp(trip_id: int, user: SecurityDep, res: TripUserLinkRsvp, session: SessionDep):
    link = session.get(TripUserLink, (trip_id, user.id))
    if not link:
        raise HTTPException(status_code=404, detail="Link Not Found")
    rsvp = res.model_dump(exclude_unset=True)
    updated_link = link.sqlmodel_update(rsvp)
    session.add(updated_link)
    session.commit()
    session.refresh(updated_link)
    return {"data": updated_link}


@router.post('/{trip_id}/cars/{car_id}/passengers', response_model=DTO[PassengerCreate], dependencies=[Depends(get_current_user)])
def add_passenger(trip_id: int, car_id: int, user: SecurityDep, passenger: PassengerCreate, session: SessionDep):
    car = session.get(Car, car_id)
    if not car or car.trip_id != trip_id:
        raise HTTPException(404, "Car not found on this trip")

    user = session.get(User, user.id)
    if not user:
        raise HTTPException(404, "User not found")
    new_passenger = Passenger(**passenger.model_dump(),
                              user_id=user.id, car_id=car_id)
    session.add(new_passenger)
    session.commit()
    session.refresh(new_passenger)
    print(car.passengers)
    return {"data": new_passenger}


@router.get('/{trip_id}/cars/{car_id}/passengers', response_model=DTO[List[Passenger]])
def get_passengers(trip_id: int, car_id: int, session: SessionDep):
    car = session.get(Car, car_id)
    if not car or car.trip_id != trip_id:
        raise HTTPException(404, "Car not found on this trip")
    session.refresh(car)
    print(f"printing car {car}")
    return {"data": car.passengers}
