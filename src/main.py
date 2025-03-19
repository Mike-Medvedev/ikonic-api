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


ikonic_db_connection = sqlite3.connect('ikonic.db', check_same_thread=False)
cursor = ikonic_db_connection.cursor()


# cursor.execute(
#     'CREATE TABLE trips(id INTEGER PRIMARY KEY AUTOINCREMENT, title, start_date, end_date, mountain)')
# ikonic_db_connection.commit()
# cursor.execute("DROP TABLE users")
# cursor.execute(
#     """CREATE TABLE users(user_id, username, password, firstname, lastname, phone_number)""")
# cursor.execute("DROP TABLE trips_users_mapping")
# cursor.execute("""CREATE TABLE trips_users_mapping(trip_id, user_id, PRIMARY KEY (trip_id, user_id),
#   FOREIGN KEY (trip_id) REFERENCES trips(id),
#   FOREIGN KEY (user_id) REFERENCES users(id))""")

# res = cursor.execute(
#     "SELECT * FROM users")
# print(res.fetchall())
# ikonic_db_connection.commit()


@app.get('/')
def index():
    return "Hello World"


class User(BaseModel):
    username: str
    password: str


@app.post('/login')
async def login(user: User):
    username = user.username
    password = user.password

    if not username or not password:
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
        return {"message": "Login Successful", "user_id": user_id}
    else:
        raise HTTPException(status_code=401, detail="Account not found")


@app.get('/profile/{user_id}')
async def profile(user_id: str):
    res = cursor.execute(
        """ SELECT firstname, lastname, phone_number FROM users WHERE user_id = ? """, (user_id, ))
    row = res.fetchone()
    return {"profile_data": {"firstname": row[0], "lastname": row[1], "phone_number": row[2]}}


@app.post('/create-trip')
async def create_trip(request: Request):
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

    return {"message": "Trip created successfully", "trip_id": trip_id}


@app.get('/get-trips')
async def get_trips(request: Request):
    headers = request.headers
    user_id = headers.get("authorization")
    if not user_id:
        raise HTTPException(
            status_code=401, detail="Missing Authorization Header")
    res = cursor.execute("""SELECT trips.* FROM trips JOIN trips_users_mapping ON trips.id
                         = trips_users_mapping.trip_id WHERE trips_users_mapping.user_id = ?""", (user_id, ))
    row = res.fetchall()
    print(row)
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
    if not trip_id:
        raise HTTPException(
            status_code=400, detail="Please select a valid trip id")
    cursor.execute("DELETE FROM trips where id = ?", (trip_id, ))
    ikonic_db_connection.commit()


@app.post('/invite')
async def invite_user(request: Request):
    body = await request.json()
    user_id = body["user_id"]
    deep_link = body["deep_link"]
    print(user_id, deep_link)
    if not user_id:
        raise HTTPException(
            status_code=400, detail="Please provide a user_id when inviting")
    message = SmsMessage(
        to=os.getenv("TO_NUMBER"),
        from_=os.getenv("VONAGE_BRAND_NAME"),
        text=f"You Have been invited to a trip, click here to RSVP, {deep_link}",
    )

    response: SmsResponse = client.sms.send(message)
    print(response)


@app.post('/rsvp')
async def rsvp(request: Request):
    body = await request.json()
    user_id = body["user_id"]
    trip_id = body["trip_id"]
    user_response = body["user_response"]
    print(user_id, user_response)
    if not user_id or not trip_id or not user_response:
        raise HTTPException(
            status_code=400, detail="Please provide the correct payload when rsvping")
    cursor.execute(
        """
    INSERT OR IGNORE INTO trips_users_mapping (trip_id, user_id)
    VALUES (?, ?)
    """,
        (trip_id, user_id)
    )
    ikonic_db_connection.commit()
    res = cursor.execute("SELECT * FROM trips_users_mapping")

    print(res.fetchall())
