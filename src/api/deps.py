from functools import lru_cache
from typing import Annotated, Generator
from sqlmodel import Session
from fastapi import Depends
from vonage import Auth, Vonage
from vonage_sms import SmsMessage, SmsResponse
from src.core.db import engine
from src.core.config import settings


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


@lru_cache(maxsize=1)  # caches instance creating a singleton
def get_vonage_client() -> Vonage:
    return Vonage(Auth(
        api_key=settings.VONAGE_API_KEY,
        api_secret=settings.VONAGE_API_SECRET)
    )


VonageDep = Annotated[Vonage, Depends(get_vonage_client)]


# add validaiton to numbers everywher with pydantic and put this in dedicated service
def send_sms_invte(phone: str, deep_link: str, client: Vonage) -> SmsResponse:
    message = SmsMessage(
        to=phone,
        from_=settings.VONAGE_NUMBER,
        text=f"You Have been invited to a trip, click here to RSVP, {deep_link}",
    )

    response: SmsResponse = client.sms.send(message)
    return response
