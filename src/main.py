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
#   PRIMARY KEY (trip_id, user_id),
#   FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
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
# ikonic_db_connection.commit()


@app.get('/')
def index():
    return "Hello World"


class User(BaseModel):
    username: str
    password: str


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
        return {"message": "Login Successful", "user_id": user_id}
    else:
        ikonic_db_connection.close()
        raise HTTPException(status_code=401, detail="Account not found")


@app.get('/profile/{user_id}')
async def profile(user_id: str):
    ikonic_db_connection = sqlite3.connect(
        'ikonic.db', check_same_thread=False)
    cursor = ikonic_db_connection.cursor()
    res = cursor.execute(
        """ SELECT firstname, lastname, phone_number FROM users WHERE user_id = ? """, (user_id, ))
    row = res.fetchone()
    ikonic_db_connection.close()
    return {"profile_data": {"firstname": row[0], "lastname": row[1], "phone_number": row[2]}}


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
            SELECT users.*, trips_users_mapping.rsvp 
            FROM users
            JOIN trips_users_mapping ON users.user_id = trips_users_mapping.user_id
            WHERE trips_users_mapping.trip_id = ?
        """, (selectedTrip,))

        invited_users = rows.fetchall()
        print(f"HERE ARE THE TRIPS USERS MAPPING ROWS --> {invited_users}")

        rsvp_groups = {"going": [], "maybe": [], "not going": []}

        for user in invited_users:
            status = user["rsvp"]
            if status in rsvp_groups:
                rsvp_groups[status].append({
                    "user_id": user["user_id"],
                    "firstname": user["firstname"],
                    "lastname": user["lastname"],
                    "phone_number": user["phone_number"],
                    "rsvp": status
                })

        ikonic_db_connection.close()

        return {
            "invited_users": {
                "going": rsvp_groups["going"],
                "maybe": rsvp_groups["maybe"],
                "not_going": rsvp_groups["not going"]
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
        "INSERT INTO trips (title, mountain, start_date, end_date) VALUES (?, ?, ?, ?)",
        (title, mountain, start_date, end_date)
    )
    trip_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO trips_users_mapping (trip_id, user_id) VALUES (?, ?)",
        (trip_id, user_id)
    )
    ikonic_db_connection.commit()
    print(data)
    ikonic_db_connection.close()
    return {"message": "Trip created successfully", "trip_id": trip_id}


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
    print(row)
    ikonic_db_connection.close()
    return {"trips": [
        {
            "id": trip[0],
            "title": trip[1],
            "startDate": trip[2],
            "endDate": trip[3],
            "mountain": trip[4]
        }
        for trip in row
    ]
    }


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
    deep_link = body["deep_link"]
    print(user, deep_link)
    if not user or not phone_number:
        raise HTTPException(
            status_code=400, detail="Please provide a user when inviting")
    message = SmsMessage(
        to=phone_number,
        from_=os.getenv("VONAGE_BRAND_NAME"),
        text=f"You Have been invited to a trip, click here to RSVP, {deep_link}",
    )

    response: SmsResponse = client.sms.send(message)
    print(response)
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
        print(user_id, trip_id, user_response)
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
        res = cursor.execute("SELECT * FROM trips_users_mapping")

        print(res.fetchall())
        ikonic_db_connection.close()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="RSVP Error") from e
    finally:
        ikonic_db_connection.close()
