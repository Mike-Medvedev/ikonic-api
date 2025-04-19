from functools import lru_cache
from typing import Annotated, Generator
from sqlmodel import Session
from fastapi import Depends, HTTPException
from vonage import Auth, Vonage
from vonage_sms import SmsMessage, SmsResponse
from src.core.db import engine
from src.core.config import settings
from supabase import create_client, Client
from gotrue.types import User
from gotrue.errors import AuthApiError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


@lru_cache(maxsize=1)  # caches function result
def get_vonage_client() -> Vonage:
    return Vonage(
        Auth(api_key=settings.VONAGE_API_KEY, api_secret=settings.VONAGE_API_SECRET)
    )


VonageDep = Annotated[Vonage, Depends(get_vonage_client)]


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    supabase: Client = create_client(
        supabase_key=settings.SUPABASE_KEY, supabase_url=settings.SUPABASE_URL
    )
    return supabase


SupabaseDep = Annotated[Client, Depends(get_supabase_client)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    supabase: SupabaseDep,
) -> User | None:
    token = credentials.credentials
    error = HTTPException(
        status_code=401, detail="Invalid or expired authentication token"
    )
    try:
        user_response = supabase.auth.get_user(token)
    except AuthApiError as exc:
        raise error from exc
    if not user_response.user:
        raise error
    return user_response.user


SecurityDep = Annotated[User, Depends(get_current_user)]

# add validaiton to numbers everywher with pydantic and put this in dedicated service


def send_sms_invte(phone: str, deep_link: str, client: Vonage) -> SmsResponse:
    message = SmsMessage(
        to=phone,
        from_=settings.VONAGE_NUMBER,
        text=f"You Have been invited to a trip, click here to RSVP, {deep_link}",
    )

    response: SmsResponse = client.sms.send(message)
    return response
