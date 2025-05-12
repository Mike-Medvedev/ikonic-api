"""FastAPI endpoints for querying and mutating friendship entities."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import and_, or_, select

from core.exceptions import ResourceNotFoundError
from models.friendship import (
    FriendshipCreate,
    FriendshipPublic,
    Friendships,
    FriendshipStatus,
    FriendshipUpdate,
)
from models.shared import DTO
from models.user import (
    User,
    UserPublic,
)
from src.api.deps import SecurityDep, SessionDep, get_current_user

router = APIRouter(prefix="/friendships", tags=["friendships"])

logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=DTO[list[UserPublic]],
)
def get_friends(session: SessionDep, user: SecurityDep) -> dict:
    """Fetch a friends list for a specific friend."""
    user: User = session.get(User, user.id)
    if not user:
        raise ResourceNotFoundError("User", user.id)
    return {"data": user.friends}


@router.post("/", dependencies=[Depends(get_current_user)], response_model=DTO[bool])
def create_friend_request(
    friendship_create: FriendshipCreate, session: SessionDep
) -> dict:
    """Create friend request."""
    requestor = session.get(User, friendship_create.user_id)
    requestee = session.get(User, friendship_create.friend_id)

    if not requestor or not requestee:
        raise ResourceNotFoundError(
            "user",
            friendship_create.user_id if not requestor else friendship_create.friend_id,
        )

    id1, id2 = sorted([friendship_create.user_id, friendship_create.friend_id])

    # Check if friendship already exists
    stmt = select(Friendships).where(
        and_(Friendships.user_id == id1, Friendships.friend_id == id2)
    )
    existing_friendship = session.exec(stmt).first()

    if existing_friendship:
        raise HTTPException(
            status_code=400, detail="Users are already friends or request is pending."
        )

    # Create new friendship record
    new_friendship = Friendships(
        user_id=id1,
        friend_id=id2,
        initiator_id=friendship_create.initiator_id,
    )

    session.add(new_friendship)
    session.commit()

    return {"data": True}


@router.get(
    "/{user_id}",
    dependencies=[Depends(get_current_user)],
    response_model=DTO[list[FriendshipPublic]],
)
def check_friend_requests(user_id: str, session: SessionDep) -> dict:
    """Check any pending friend requests (outgoing or incoming) for a given user id."""
    user = session.get(User, user_id)
    if not user:
        raise ResourceNotFoundError("User", user_id)

    stmt = select(Friendships).where(
        and_(
            or_(
                Friendships.user_id == user.id,
                Friendships.friend_id == user.id,
            ),
            # Friendships.initiator_id != user.id,
            Friendships.status == FriendshipStatus.PENDING,
        )
    )

    results = session.exec(stmt).all()
    return {"data": results}


@router.patch("/", dependencies=[Depends(get_current_user)], response_model=DTO[bool])
def response_friend_request(
    user: SecurityDep, friendship_update: FriendshipUpdate, session: SessionDep
) -> dict:
    """Handle a friend request response."""
    user = session.get(User, user.id)
    if not user:
        raise ResourceNotFoundError("User", user.id)

    id1, id2 = sorted([friendship_update.user_id, friendship_update.friend_id])

    friendship_to_update = session.exec(
        select(Friendships).where(
            and_(Friendships.user_id == id1, Friendships.friend_id == id2)
        )
    ).first()
    if not friendship_to_update:
        raise ResourceNotFoundError("Friendship", (id1, id2))
    if friendship_to_update.initiator_id == user.id:
        raise HTTPException(400, detail="Cannot accept your own friend request.")
    # Ensure the current user is involved in this friendship
    if user.id not in (friendship_update.user_id, friendship_update.friend_id):
        raise HTTPException(
            status_code=403,
            detail="You can only update friendship requests you're involved in.",
        )
    friendship_to_update.status = friendship_update.status
    session.add(friendship_to_update)
    session.commit()

    return {"data": True}
