from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel


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

# cursor.execute("CREATE TABLE users(name, password)")
# cursor.execute("""INSERT INTO users VALUES ('Mike', 'dummy')""")
# ikonic_db_connection.commit()
# res = cursor.execute('SELECT ROWID, name, password FROM users')
# print(res.fetchall())
# cursor.execute(
#     'CREATE TABLE trips(id INTEGER PRIMARY KEY, title, start_date, end_date, mountain)')
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
def login(user: User):
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
