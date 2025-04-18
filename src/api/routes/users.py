from typing import List
import uuid
from fastapi import APIRouter, Depends
from sqlmodel import select
from src.models import DTO, User
from src.api.deps import SessionDep, get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get('', response_model=DTO[List[User]], dependencies=[Depends(get_current_user)])
def get_users(session: SessionDep):
    users = session.exec(select(User)).all()
    return {"data": list(users)}


@router.get('/{id}', dependencies=[Depends(get_current_user)], response_model=DTO[User])
def get_user_by_id(id: str, session: SessionDep):
    user = session.get(User, id)
    print(user)
    return {"data": user}
