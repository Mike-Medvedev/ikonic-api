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
9. Implement DTO and DAO layers to improve architecture. DTO -> data crossing from server to client , DAO -> encapsulate ORM operations USERDao

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
2. use plurals for resource names -> /items
3. nest related resources under parent -> /users/{userId}/orders/{orderId}
4. filtering/pagination/sorting go in query param -> GET /projects?status=active&page=2&per_page=20
5. keep words lower case and hyphenated for multiple words -> /user-profiles
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
13. RelationShips() and BackPopulate used to sync and auto query models, so cars have list of passengers, you can call cars.passengers and have it query list of passengers for you, and also if you creat a passenger, back populate list of passengers in the car

## DI (Dependency Injection)

### 1. DEPENDECY INVERSION PRINCIPLE: You “inject” the concrete implementation like get_vonage_client() into your function via its signature (e.g. using Depends(get_vonage_client)) rather than instantiating it inside.

# This follows the concept of Programming To An Interface, get_vonage_client is a contract, thats all endpoint cares about, exposinge the .send() method

-----> endpoint should not instantiate a client, inject it so its implementation is de coupled from endpoint, easier testing/ swapping

2. FastAPI DI system allows to declare dependencies as Depends() in endpoint functions
3. Under the hood, FastAPI will call those dependency functions (or classes) before your path operation runs, inject their return values, and handle cleanup (for generator dependencies).
4. can be used in Annotated Type Annotated[type, Depends()] or set Annotated[type, Depends()]
   to a type -> SessionDB = Annotated[Session, Depends(get_db)]

# Python EcoSystem Learnings

## VENV

1. VENV is a virtual environment in python used to isolate dependencies and python versions to a specific workspace. Python installs packages globally by default, therefore multiple projects will require different versions of packages and theree will be conflicts
2. Venv has an activate script that puts itself onto the $PATH and references to python or dependencies point to the venv $PATH instead of the global path
3. Venv contains a bin directory which contains binaries of executables like python or other deps installed, you can run them directly in the CLI. python is usually symlinked to the actual intepreter python3.13 which is the actual python binary
4. The Lib directory includes sites_packages which contains the actual working directory of installed packages in your workspace (node_modules for python)

## pyproject.toml and drawbacks of requirements.txt and pip install

1. Pip install is the original dependency manager but it doesnt produce a reproducible lock file. requirements.txt is bad, doesnt
   include sub dependencies or do any resolutions
2. pyproject.toml is like package.json is contains meta data and lists all the dependencies your project needs. It also contains
   other project specific data like configs to build the system [build-system] and [projects.scripts] to establish CLI commands in the workspace
3. The only required tables as part of pep 621 is [project] and [build-system]
4. PyProject.toml can also specify Dependency Groups like dev or lint which will include groups of packages that can be installed
   with a single command for things like CI

## package managers

1. A package manager is a tool that is used to manage dependencies in a project.
2. Its crucial because of the idea that dependencies themselves rely on sub dependencies, and multiple deps may conflict on what version of deps they use.
3. Package resolution is the recursive process of finding the right version of a dep to satisfy all deps and sub deps. Its an NP-Hard problem at worst case
4. Package managers will generally use your pyproject.toml to identify which deps should be installed.
5. Deps are installed -> Dep versions are resolved -> the actual dependency resolutions are written to a lock file and their versions are pinned
6. LockFile is crucial and submitted to version control to allow anyone to reproduce the exact snapshot of deps and their subdeps & versions

## Dev Tools

1. Dev tools are crucial for creating a consistent and beautiful codebase that users can adopt and maintain a consisten look across
   all developers
2. Dev tools like package managers can manage your venv, syncing the pyproject.toml deps to a lock file. They
   also will manage deps so you use their CLI to add, remove, upgrade packages and run tools.
3. Use Dev tools like uv or pdm to ensure when you install, or use deps, they are in the context of the env, the correct path,
   the correct binary is used (OS agonistic), etc
4. Pyproject.toml is completely flexible and dev tools assign their own config to the toml. Like [project.ruff] is a custom table
   that ruff expects
