from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from vonage import Auth, Vonage
from vonage_sms import SmsMessage, SmsResponse
from dotenv import load_dotenv
import os
load_dotenv()

client = Vonage(Auth(api_key=os.getenv("VONAGE_API_KEY"),
                api_secret=os.getenv("VONAGE_API_SECRET")))


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Login = [
    ('mev', 'clat', 'michael', 'medvedev', '2038587135'),
    ('kelp', 'thar', 'john', 'roslin', '7324926329'),
    ('pit', 'pauxt', None, None, None),
    ('pf', 'chang', None, None, None),
    ('zecroy', 'menoy', None, None, None),
    ('ok', 'chris', None, None, None),
    ('ost', 'edging', None, None, None)
]


# cursor.execute(
#     'CREATE TABLE trips(id INTEGER PRIMARY KEY AUTOINCREMENT, title, start_date, end_date, mountain)')
# ikonic_db_connection.commit()
# cursor.execute("DROP TABLE users")
# cursor.execute(
#     """CREATE TABLE users(user_id, username, password, firstname, lastname, phone_number)""")
# cursor.execute("""CREATE TABLE trips_users_mapping (
#   trip_id INTEGER,
#   user_id TEXT,
#   rsvp TEXT,
#   paid INTEGER,
#   PRIMARY KEY (trip_id, user_id),
#   FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
#   FOREIGN KEY (user_id) REFERENCES users(user_id)
# );
# """)
# cursor.execute("""CREATE TABLE cars (
#   id INTEGER PRIMARY KEY AUTOINCREMENT,
#   trip_id INTEGER,
#   owner TEXT,
#   seat_count INTEGER,
#   FOREIGN KEY (trip_id) REFERENCES trips(id)
#   FOREIGN KEY (owner) REFERENCES users(user_id)
# );""")
# cursor.execute("""CREATE TABLE car_passengers (
#   car_id INTEGER,
#   user_id INTEGER,
#   seat_position INTEGER,
#   PRIMARY KEY (car_id, seat_position),
#   FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE,
#   FOREIGN KEY (user_id) REFERENCES users(user_id)
# );
# """)

# res = cursor.execute(
#     "SELECT * FROM users")
# print(res.fetchall())
# updates = [
#     ('12038587135', '2038587135'),
#     ('17324926329', '7324926329')
# ]
# cursor.executemany("""UPDATE users
#                SET phone_number = ?
#                WHERE phone_number = ?""", updates)
# res = cursor.execute("SELECT * FROM trips_users_mapping")
# print(res.fetchall())
# res3 = cursor.execute("SELECT * FROM trips")
# print(res3.fetchall())
# res2 = cursor.execute("SELECT * FROM users WHERE user_id = ?",
#                       ("6556cf1c-88e7-4f6a-bff7-b8be7d546628", ))
# # print(res2.fetchone())
# ikonic_db_connection = sqlite3.connect(
#     'ikonic.db', check_same_thread=False)
# cursor = ikonic_db_connection.cursor()
# res = cursor.execute(
#     "SELECT * FROM users")
# result = res.fetchall()
# print(result)
# ikonic_db_connection.commit()


@app.get('/')
def index():
    return "Hello World"


class User(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    user_id: Optional[str] = None


@app.post('/login')
async def login(user: User):
    ikonic_db_connection = sqlite3.connect(
        'ikonic.db', check_same_thread=False)
    cursor = ikonic_db_connection.cursor()
    username = user.username
    password = user.password

    if not username or not password:
        ikonic_db_connection.close()
        raise HTTPException(
            status_code=404, detail="Username and password are required")

    res = cursor.execute(
        "SELECT user_id, password FROM users WHERE username = ?", (username,))
    row = res.fetchone()

    if row:
        user_id, found_password = row
        if found_password.casefold() != password.casefold():
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )
        ikonic_db_connection.close()
        data = {"user_id": user_id}
        return {"message": "Login Successful", "data": data}
    ikonic_db_connection.close()
    raise HTTPException(status_code=401, detail="Account not found")


@app.get('/profile/{user_id}')
async def profile(user_id: str):
    ikonic_db_connection = sqlite3.connect(
        'ikonic.db', check_same_thread=False)
    cursor = ikonic_db_connection.cursor()
    res = cursor.execute(
        """ SELECT user_id, firstname, lastname, phone_number FROM users WHERE user_id = ? """, (user_id, ))
    row = res.fetchone()
    ikonic_db_connection.close()
    return {"data": {"user_id": row[0], "firstname": row[1], "lastname": row[2], "phone_number": row[3]}}


@app.get('/users')
def get_users():
    try:
        ikonic_db_connection = sqlite3.connect(
            'ikonic.db', check_same_thread=False)
        cursor = ikonic_db_connection.cursor()
        row = cursor.execute("SELECT * FROM users")
        users = row.fetchall()
        list_of_users = [
            {
                "user_id": user[0],
                "firstname": user[3],
                "lastname": user[4],
                "phone_number": user[5]
            } for user in users
        ]
        ikonic_db_connection.close()
        return {"users": list_of_users}
    except Exception as e:
        ikonic_db_connection.close()
        raise HTTPException(status_code=400, detail=f"{e}") from e


@app.get('/invited-users/{selectedTrip}')
def get_invited_users(selectedTrip: int):
    ikonic_db_connection = sqlite3.connect(
        'ikonic.db', check_same_thread=False)
    cursor = ikonic_db_connection.cursor()
    cursor.row_factory = sqlite3.Row
    if not selectedTrip:
        ikonic_db_connection.close()
        raise HTTPException(
            status_code=400, detail="Please provide a valid trip ID")
    try:
        rows = cursor.execute("""
            SELECT users.*, trips_users_mapping.rsvp, trips_users_mapping.paid 
            FROM users
            JOIN trips_users_mapping ON users.user_id = trips_users_mapping.user_id
            WHERE trips_users_mapping.trip_id = ?
        """, (selectedTrip,))

        invited_users = rows.fetchall()

        rsvp_groups = {"going": [], "pending": [],
                       "maybe": [], "not_going": []}

        for user in invited_users:
            status = user["rsvp"]
            if status in rsvp_groups:
                rsvp_groups[status].append({
                    "user_id": user["user_id"],
                    "firstname": user["firstname"],
                    "lastname": user["lastname"],
                    "phone_number": user["phone_number"],
                    "rsvp": status,
                    "paid": user["paid"]
                })

        ikonic_db_connection.close()

        return {
            "invited_users": {
                "going": rsvp_groups["going"],
                "pending": rsvp_groups["pending"],
                "maybe": rsvp_groups["maybe"],
                "not_going": rsvp_groups["not_going"]
            }
        }
    except Exception as e:
        print(e)
        ikonic_db_connection.close()
        raise HTTPException(status_code=400, detail=f"{e}") from e


@app.post('/create-trip')
async def create_trip(request: Request):
    ikonic_db_connection = sqlite3.connect(
        'ikonic.db', check_same_thread=False)
    cursor = ikonic_db_connection.cursor()
    user_id = request.headers.get("authorization")
    if not user_id:
        raise HTTPException(
            status_code=401, detail="Missing authorization header")
    data = await request.json()
    try:
        title = data["title"]
        mountain = data["mountain"]
        start_date = data["startDate"]
        end_date = data["endDate"]
    except KeyError as e:
        ikonic_db_connection.close()
        raise HTTPException(
            status_code=400, detail=f"Missing field in request data: {e}") from e

    cursor.execute(
        "INSERT INTO trips (title, mountain, start_date, end_date, owner) VALUES (?, ?, ?, ?, ?)",
        (title, mountain, start_date, end_date, user_id)
    )
    trip_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO trips_users_mapping (trip_id, user_id, rsvp) VALUES (?, ?, ?)",
        (trip_id, user_id, "going")
    )
    ikonic_db_connection.commit()
    ikonic_db_connection.close()
    return {"message": "Trip created successfully", "data": trip_id}


@app.get('/get-trips')
async def get_trips(request: Request):
    ikonic_db_connection = sqlite3.connect(
        'ikonic.db', check_same_thread=False)
    cursor = ikonic_db_connection.cursor()
    headers = request.headers
    user_id = headers.get("authorization")
    if not user_id:
        ikonic_db_connection.close()
        raise HTTPException(
            status_code=401, detail="Missing Authorization Header")
    res = cursor.execute("""SELECT trips.* FROM trips JOIN trips_users_mapping ON trips.id
                         = trips_users_mapping.trip_id WHERE trips_users_mapping.user_id = ?""", (user_id, ))
    row = res.fetchall()
    ikonic_db_connection.close()
    return {"data": [
        {
            "id": trip[0],
            "title": trip[1],
            "startDate": trip[2],
            "endDate": trip[3],
            "mountain": trip[4],
            "owner": trip[5],
            "image": trip[6],
            "desc": trip[7],
            "total_cost": trip[8]
        }
        for trip in row
    ]
    }


@app.get('/get-trip/{selectedTripId}')
async def get_trip(selectedTripId: str):
    ikonic_db_connection = sqlite3.connect(
        'ikonic.db', check_same_thread=False)
    cursor = ikonic_db_connection.cursor()
    # if not user_id:
    #     ikonic_db_connection.close()
    #     raise HTTPException(
    #         status_code=401, detail="Missing Authorization Header")
    res = cursor.execute(
        """SELECT * FROM trips WHERE id = ?""", (selectedTripId, ))
    trip = res.fetchone()
    ikonic_db_connection.close()
    return {"data":
            {
                "id": trip[0],
                "title": trip[1],
                "startDate": trip[2],
                "endDate": trip[3],
                "mountain": trip[4],
                "owner": trip[5],
                "image": trip[6],
                "desc": trip[7],
                "total_cost": trip[8]
            }

            }


@app.post('/{trip_id}/update-trip')
async def update_trip(trip_id: str, request: Request):
    data = await request.json()
    title = data.get("title", "")
    desc = data.get("desc", "")
    image = data.get("image", "")
    total_cost = data.get("totalCost", "")
    try:
        ikonic_db_connection = sqlite3.connect(
            'ikonic.db', check_same_thread=False)
        cursor = ikonic_db_connection.cursor()
        cursor.execute(
            """
                UPDATE trips
                SET
                title = COALESCE(NULLIF(?, ''), title),
                desc  = COALESCE(NULLIF(?, ''), desc),
                image = COALESCE(NULLIF(?, ''), image),
                total_cost = COALESCE(NULLIF(?, ''), total_cost)
                WHERE id = ?
            """,
            (title, desc, image, total_cost, trip_id)
        )

        ikonic_db_connection.commit()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=e) from e

    finally:
        ikonic_db_connection.close()
    return {"message": "Trip updated successfully"}


@app.delete('/delete-trip/{trip_id}')
def delete_post(trip_id: str):
    ikonic_db_connection = sqlite3.connect(
        'ikonic.db', check_same_thread=False)
    cursor = ikonic_db_connection.cursor()
    if not trip_id:
        ikonic_db_connection.close()
        raise HTTPException(
            status_code=400, detail="Please select a valid trip id")
    cursor.execute("DELETE FROM trips where id = ?", (trip_id, ))
    ikonic_db_connection.commit()
    ikonic_db_connection.close()


@app.post('/invite')
async def invite_user(request: Request):
    body = await request.json()
    user = body["user"]
    phone_number: str = user["phone_number"]
    user_id = user["user_id"]
    trip_id = body["trip_id"]
    deep_link = body["deep_link"]
    if not user or not phone_number:
        raise HTTPException(
            status_code=400, detail="Please provide a user when inviting")
    message = SmsMessage(
        to=phone_number,
        from_=os.getenv("VONAGE_BRAND_NAME"),
        text=f"You Have been invited to a trip, click here to RSVP, {deep_link}",
    )

    response: SmsResponse = client.sms.send(message)
    try:
        ikonic_db_connection = sqlite3.connect(
            'ikonic.db', check_same_thread=False)
        cursor = ikonic_db_connection.cursor()
        cursor.execute("UPDATE trips_users_mapping SET rsvp = ? WHERE trip_id = ? AND user_id = ?",
                       ("pending", trip_id, user_id,))
        ikonic_db_connection.commit()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="RSVP Error") from e
    finally:
        ikonic_db_connection.close()
    return {"response": "success"}


@app.post('/rsvp')
async def rsvp(request: Request):
    try:
        ikonic_db_connection = sqlite3.connect(
            'ikonic.db', check_same_thread=False)
        cursor = ikonic_db_connection.cursor()
        body = await request.json()
        user_id = request.headers.get("authorization")
        trip_id = body["trip_id"]
        user_response = body["user_response"]
        if not user_id or not trip_id or not user_response:
            ikonic_db_connection.close()
            raise HTTPException(
                status_code=400, detail="Please provide the correct payload when rsvping")
        cursor.execute(
            """
            INSERT INTO trips_users_mapping (trip_id, user_id, rsvp)
            VALUES (?, ?, ?)
            ON CONFLICT(trip_id, user_id) DO UPDATE SET rsvp = excluded.rsvp;
        """,
            (int(trip_id), user_id, user_response)
        )
        ikonic_db_connection.commit()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="RSVP Error") from e
    finally:
        ikonic_db_connection.close()


@app.get('/{trip_id}/cars')
def get_cars_for_trip(trip_id: int):
    try:
        ikonic_db_connection = sqlite3.connect(
            'ikonic.db', check_same_thread=False)
        cursor = ikonic_db_connection.cursor()
        cursor.row_factory = sqlite3.Row
        # rows = cursor.execute(
        #         """
        #         SELECT
        #             cars.id AS car_id,
        #             cars.trip_id,
        #             cars.owner,
        #             cars.seat_count,
        #             car_passengers.seat_position,
        #             users.user_id,
        #             users.firstname,
        #             users.lastname,
        #             users.phone_number
        #         FROM cars
        #         LEFT JOIN car_passengers ON cars.id = car_passengers.car_id
        #         LEFT JOIN users ON car_passengers.user_id = users.user_id
        #         WHERE cars.trip_id = ?
        #         """, (trip_id, )
# )
        rows = cursor.execute("""
                              SELECT cars.id, cars.trip_id, cars.owner, cars.seat_count
                              FROM cars
                              WHERE cars.trip_id = ?""", (trip_id, ))
        fetched_cars = rows.fetchall()
        cars = [dict(car) for car in fetched_cars]
        retrieved_cars = []
        for car in cars:
            res = cursor.execute("""
                        SELECT
                            car_passengers.seat_position,
                            users.user_id, 
                            users.firstname, 
                            users.lastname, 
                            users.phone_number
                        FROM car_passengers
                        JOIN users ON car_passengers.user_id = users.user_id
                        WHERE car_passengers.car_id = ?""", (car["id"], ))
            passengers = res.fetchall()
            result = {**car, "passengers": passengers}
            retrieved_cars.append(result)
        return retrieved_cars
    except Exception as e:
        raise HTTPException(status_code=400, detail=e) from e
    finally:
        ikonic_db_connection.close()


class Car(BaseModel):
    car_id: int
    owner: User
    passengers: List[User]
    seatCount: int


class NewCar(BaseModel):
    owner: User
    seatCount: int


@app.post('/{trip_id}/create-car')
def create_car(trip_id: int, car: NewCar):
    try:
        ikonic_db_connection = sqlite3.connect(
            'ikonic.db', check_same_thread=False)
        cursor = ikonic_db_connection.cursor()
        cursor.execute("INSERT INTO cars (trip_id, owner, seat_count) VALUES (?, ?, ?)",
                       (trip_id, car.owner.user_id, car.seatCount))
        generated_id = cursor.lastrowid
        new_car: Car = {"car_id": generated_id, "owner": car.owner,
                        "passengers": [], "seat_count": car.seatCount}
        ikonic_db_connection.commit()
        return new_car
    except Exception as e:
        raise HTTPException(status_code=400, detail=e) from e
    finally:
        ikonic_db_connection.close()


@app.delete('/{car_id}/delete-car')
def delete_car_from_trip(car_id: int):
    try:
        ikonic_db_connection = sqlite3.connect(
            'ikonic.db', check_same_thread=False)
        cursor = ikonic_db_connection.cursor()
        cursor.execute("DELETE FROM cars WHERE id = ?", (car_id, ))
        ikonic_db_connection.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=e) from e
    finally:
        ikonic_db_connection.close()


@app.post('/{car_id}/{user_id}/{seat_position}/add-passenger')
def add_passenger(car_id: int, user_id: str, seat_position: int):
    """Adds a User to a car as a passenger in a specific seat"""
    try:
        ikonic_db_connection = sqlite3.connect(
            'ikonic.db', check_same_thread=False)
        cursor = ikonic_db_connection.cursor()
        cursor.execute(
            """INSERT INTO car_passengers (car_id, user_id, seat_position) VALUES (?, ?, ?)
            ON CONFLICT(car_id, seat_position) DO UPDATE SET user_id = excluded.user_id;""", (car_id, user_id, seat_position, ))
        ikonic_db_connection.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=e) from e
    finally:
        ikonic_db_connection.close()


@app.post('/{trip_id}/{user_id}/update-paid')
async def update_paid_status(trip_id: str, user_id: str, request: Request):
    data = await request.json()
    if "new_status" not in data:
        raise HTTPException(
            status_code=400, detail="Error: no new_status given")

    new_status = data["new_status"]
    try:
        ikonic_db_connection = sqlite3.connect(
            'ikonic.db', check_same_thread=False)
        cursor = ikonic_db_connection.cursor()
        cursor.execute(
            "UPDATE trips_users_mapping SET paid = ? WHERE trip_id = ? AND user_id = ?", (int(new_status), trip_id, user_id))
        ikonic_db_connection.commit()
    except Exception as e:
        print(e)
        raise HTTPException(detail=400, status_code=e) from e
    finally:
        ikonic_db_connection.close()
    return {"message": "Successfully Updated"}


@app.post('/{user_id}/update-phone')
async def update_phone_number(user_id: str, request: Request):
    data = await request.json()
    if "phone_number" not in data:
        raise HTTPException(
            status_code=400, detail="Error: no new_status given")

    new_phone_number = data["phone_number"]
    try:
        ikonic_db_connection = sqlite3.connect(
            'ikonic.db', check_same_thread=False)
        cursor = ikonic_db_connection.cursor()
        cursor.execute(
            "UPDATE users SET phone_number = ? WHERE user_id = ?", (new_phone_number, user_id))
        ikonic_db_connection.commit()
    except Exception as e:
        print(e)
        raise HTTPException(detail=400, status_code=e) from e
    finally:
        ikonic_db_connection.close()
    return {"message": "Successfully Updated"}
