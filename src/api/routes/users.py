from typing import List
import uuid
from fastapi import APIRouter
from sqlmodel import select
from src.models import DTO, User
from src.api.deps import SessionDep

router = APIRouter(prefix="/users", tags=["users"])


@router.get('/', response_model=DTO[List[User]])
def get_users(session: SessionDep):
    users = session.exec(select(User)).all()
    return {"data": list(users)}


@router.get('/{id}')
def get_user_by_id(id: str, session: SessionDep):
    _id = uuid.UUID(id)
    user = session.get(User, _id)
    return user
