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
    # ikonic_db_connection = sqlite3.connect(
    #     'ikonic.db', check_same_thread=False)
    # cursor = ikonic_db_connection.cursor()
    # user_id = request.headers.get("authorization")
    # if not user_id:
    #     raise HTTPException(
    #         status_code=401, detail="Missing authorization header")
    # data = await request.json()
    # try:
    #     title = data["title"]
    #     mountain = data["mountain"]
    #     start_date = data["startDate"]
    #     end_date = data["endDate"]
    # except KeyError as e:
    #     ikonic_db_connection.close()
    #     raise HTTPException(
    #         status_code=400, detail=f"Missing field in request data: {e}") from e

    # cursor.execute(
    #     "INSERT INTO trips (title, mountain, start_date, end_date, owner) VALUES (?, ?, ?, ?, ?)",
    #     (title, mountain, start_date, end_date, user_id)
    # )
    # trip_id = cursor.lastrowid
    # cursor.execute(
    #     "INSERT INTO trips_users_mapping (trip_id, user_id, rsvp) VALUES (?, ?, ?)",
    #     (trip_id, user_id, "accepted")
    # )
    # ikonic_db_connection.commit()
    # ikonic_db_connection.close()
    return {"message": "Trip created successfully", "data": trip.id}


@router.get('/', response_model=DTO[List[TripPublic]])
def get_trips(session: SessionDep):
    user_id = "e25b2f98-f6e0-4a54-84f6-16f42cb849b4"
    query = select(Trip).join(TripUserLink, Trip.id == TripUserLink.trip_id).where(
        TripUserLink.user_id == user_id)
    trips = session.exec(query).all()
    return {"data": trips}
    # ikonic_db_connection = sqlite3.connect(
    #     'ikonic.db', check_same_thread=False)
    # cursor = ikonic_db_connection.cursor()
    # headers = request.headers
    # user_id = headers.get("authorization")
    # if not user_id:
    #     ikonic_db_connection.close()
    #     raise HTTPException(
    #         status_code=401, detail="Missing Authorization Header")
    # res = cursor.execute("""SELECT trips.* FROM trips JOIN trips_users_mapping ON trips.id
    #                      = trips_users_mapping.trip_id WHERE trips_users_mapping.user_id = ?""", (user_id, ))
    # row = res.fetchall()
    # ikonic_db_connection.close()
    # return {"data": [
    #     {
    #         "id": trip[0],
    #         "title": trip[1],
    #         "startDate": trip[2],
    #         "endDate": trip[3],
    #         "mountain": trip[4],
    #         "owner": trip[5],
    #         "image": trip[6],
    #         "desc": trip[7],
    #         "total_cost": trip[8]
    #     }
    #     for trip in row
    # ]
    # }


@router.get('/{id}', response_model=DTO[TripPublic])
async def get_trip(id: int, session: SessionDep):
    trip = session.get(Trip, id)
    return {"data": trip}
    # ikonic_db_connection = sqlite3.connect(
    #     'ikonic.db', check_same_thread=False)
    # cursor = ikonic_db_connection.cursor()
    # # if not user_id:
    # #     ikonic_db_connection.close()
    # #     raise HTTPException(
    # #         status_code=401, detail="Missing Authorization Header")
    # res = cursor.execute(
    #     """SELECT trips.*, users.* FROM trips JOIN users ON users.user_id = trips.owner WHERE trips.id = ?""", (selectedTripId,))
    # trip = res.fetchone()
    # ikonic_db_connection.close()
    # return {"data":
    #         {
    #             "id": trip[0],
    #             "title": trip[1],
    #             "startDate": trip[2],
    #             "endDate": trip[3],
    #             "mountain": trip[4],
    #             "owner": {
    #                 "user_id": trip[9],
    #                 "firstname": trip[12],
    #                 "lastname": trip[13],
    #                 "phone_number": trip[14]
    #             },
    #             "image": trip[6],
    #             "desc": trip[7],
    #             "total_cost": trip[8]
    #         }

    #         }


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
    # data = await request.json()
    # title = data.get("title", "")
    # desc = data.get("desc", "")
    # image = data.get("image", "")
    # total_cost = data.get("totalCost", "")
    # try:
    #     ikonic_db_connection = sqlite3.connect(
    #         'ikonic.db', check_same_thread=False)
    #     cursor = ikonic_db_connection.cursor()
    #     cursor.execute(
    #         """
    #             UPDATE trips
    #             SET
    #             title = COALESCE(NULLIF(?, ''), title),
    #             desc  = COALESCE(NULLIF(?, ''), desc),
    #             image = COALESCE(NULLIF(?, ''), image),
    #             total_cost = COALESCE(NULLIF(?, ''), total_cost)
    #             WHERE id = ?
    #         """,
    #         (title, desc, image, total_cost, trip_id)
    #     )

    #     ikonic_db_connection.commit()
    # except Exception as e:
    #     print(e)
    #     raise HTTPException(status_code=400, detail=e) from e

    # finally:
    #     ikonic_db_connection.close()
    # return {"message": "Trip updated successfully"}


@router.delete('/{id}')
def delete_post(id: int, session: SessionDep):
    trip_db = session.get(Trip, id)
    if not trip_db:
        raise HTTPException(status_code=404, detail="Trip Not Found")
    session.delete(trip_db)
    session.commit()
    return {"data": True}
    # ikonic_db_connection = sqlite3.connect(
    #     'ikonic.db', check_same_thread=False)
    # cursor = ikonic_db_connection.cursor()
    # if not trip_id:
    #     ikonic_db_connection.close()
    #     raise HTTPException(
    #         status_code=400, detail="Please select a valid trip id")
    # cursor.execute("DELETE FROM trips where id = ?", (trip_id, ))
    # ikonic_db_connection.commit()
    # ikonic_db_connection.close()


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
