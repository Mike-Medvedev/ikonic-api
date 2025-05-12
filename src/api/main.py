"""Group all API Routers and respective endpoints."""

from fastapi import APIRouter

from api.routes import cars, friendships, invites, trips, users

api_router = APIRouter()


@api_router.get("/")
def main() -> str:
    """Root API endpoint."""
    return "Hello World!"


api_router.include_router(users.router)
api_router.include_router(trips.router)
api_router.include_router(cars.router)
api_router.include_router(invites.router)
api_router.include_router(friendships.router)
