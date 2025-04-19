from fastapi import APIRouter

from src.api.routes import trips, users

api_router = APIRouter()


@api_router.get("/")
def main():
    return "Hello World!"


api_router.include_router(users.router)
api_router.include_router(trips.router)
