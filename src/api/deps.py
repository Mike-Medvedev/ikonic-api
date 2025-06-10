"""Defines Dependencies to be injected into FastAPI endpoints."""

from collections.abc import Generator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from gotrue.errors import AuthApiError
from gotrue.types import User
from sqlmodel import Session
from supabase import Client, create_client
from vonage import Auth, Vonage
from vonage_sms import SmsMessage, SmsResponse

from src.core.config import settings
from src.core.db import engine
from src.core.exceptions import InvalidTokenError

security = HTTPBearer()


def get_db() -> Generator[Session]:
    """Return a DB session."""
    with Session(engine) as session:
        yield session


# For use in endpoint params to inject db session
SessionDep = Annotated[Session, Depends(get_db)]


@lru_cache(maxsize=1)  # caches function result
def get_vonage_client() -> Vonage:
    """Return Vonage Client."""
    return Vonage(
        Auth(api_key=settings.VONAGE_API_KEY, api_secret=settings.VONAGE_API_SECRET)
    )


VonageDep = Annotated[Vonage, Depends(get_vonage_client)]


def get_supabase_client() -> Client:
    """Return Supabase client."""
    supabase: Client = create_client(
        supabase_key=settings.SUPABASE_KEY, supabase_url=settings.SUPABASE_URL
    )
    return supabase


SupabaseDep = Annotated[Client, Depends(get_supabase_client)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    supabase: SupabaseDep,
) -> User | None:
    """Extract bearer token and validate it with supabase client. Return Validated User data."""
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
    except AuthApiError as exc:
        resource = "Token"
        raise InvalidTokenError(resource, "12345") from exc
    if not user_response.user:
        raise InvalidTokenError(resource, "12345")
    return user_response.user


SecurityDep = Annotated[User, Depends(get_current_user)]

# add validaiton to numbers everywher with pydantic and put this in dedicated service


def send_sms_invte(phone: str, deep_link: str, client: Vonage) -> SmsResponse:
    """Text an rsvp link to an invited user."""
    message = SmsMessage(
        to=phone,
        from_=settings.VONAGE_NUMBER,
        text=f"You Have been invited to a trip, click here to RSVP, {deep_link}",
    )

    response: SmsResponse = client.sms.send(message)
    return response
