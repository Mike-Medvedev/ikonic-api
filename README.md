learnings from from fastapi template

## Project Setup Learnings

1. .env file placed in root directory, can specify relative path in Config
2. requirements.txt placed in root of backend directory
3. although optional, **init**.py is used to specify package as module
4. main.py contains FastAPI app init
5. test folder for tests, core folder for config/db/security, crucial files
6. api folder for actual endpoints/routes (controller)
7. services for business logic in seperate class (services)
8. db operations in data access layer
9. Implement DTO and DAO layers to improve architecture. DTO -> data crossing from server to client , DAO -> encapusalte ORM operations USERDao

## SETTING/CONFIG Learnings

1. FastAPI settings extend pydantic Base Settings model
2. Pydantic automatically pulls from .env and you can define each env as a property of the model and run validation/custom logic with Annotated
3. The @computer_field property means a python method is registered/visible by pydantic as part of the models property
4. The @property means a python method can be accessed with dot notation on a class, like foo.bar() -> foo.bar
5. Annotated Type can is a typehint to be used to add metadata or even custom logic -> Annotated[typehint, function to perform on type]
6. Secrets like DB password can come from secrets
7. DB connection string built from builder func

## Routing/OpenAPI learnings

1. endpoint names are nouns not verbs i.e (/users ) AVOID (/getUsers)
2. use pluralals for resource names -> /items
3. nest related resources under parent -> /users/{userId}/orders/{orderId}
4. filtering/pagination/sorting go in query param -> GET /projects?status=active&page=2&per_page=20
5. keep words lower case and hyphentated for multiple words -> /user-profiles
6. use correct http method -> (put and patch)
7. api/v1 prepended to all routes per OpenAPI spec, making backwards compatibility easy -> api/v2

## Database/ORM learnings

1. ORM is awesome because it maps DB schema to Python Objects
2. ORM streamlines querying and improves debugging, relationships between schema, maintanability, consistency, no raw SQL queries
3. SQLModel is built ontop of SQLAlchemy and pydantic, combining ORM capabilities with type hints/validation
4. DB schema is defined as Classes extending SQLModel, pydantic types used to define types
5. Field() behaves like @dataclass, avoids manual **init**() self.data = data and defines properties as class fields
6. Field() also takes meta data and does validation during pydantic validation
7. create_engine() creates a session for using ORM objects and interacting with the DB
8. DB engine creation in db.py along with init() function which is used for db seeding -> providing init data in new DB's
9. Alembic can be used for migrations which is correct way for version control of DB
10. Different models are used for different parts -> UserPublic is what API returns, UserUpdate is what API recieves when client sends User Update, different types
11. Supabase is managed PostgresSQL db on cloud and psycopg used as driver to connect db to sqlalchemy engine
12. information_schema for querying schema info in postgres,

## DI (Dependency Injection)

1. FastAPI DI system allows to declare dependencies as Depends() in endpoint functions
2. Under the hood, FastAPI will call those dependency functions (or classes) before your path operation runs, inject their return values, and handle cleanup (for generator dependencies).
3. can be used in Annotated Type Annotated[type, Depends()] or set Annotated[type, Depends()]
   to a type -> SessionDB = Annotated[Session, Depends(get_db)]
