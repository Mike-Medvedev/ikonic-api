from fastapi import APIRouter

from src.api.routes import cars, trips, users

api_router = APIRouter()


@api_router.get("/")
def main():
    return "Hello World!"


api_router.include_router(users.router)
api_router.include_router(trips.router)
api_router.include_router(cars.router)
