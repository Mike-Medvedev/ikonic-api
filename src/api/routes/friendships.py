"""FastAPI endpoints for querying and mutating friendship entities."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import and_, func, or_, select

from core.exceptions import ResourceNotFoundError
from models.friendship import (
    FriendRequestType,
    FriendshipCreate,
    FriendshipPublic,
    Friendships,
    FriendshipStatus,
    FriendshipUpdate,
)
from models.shared import DTO
from models.user import (
    User,
    UserWithFriendshipInfo,
)
from src.api.deps import SecurityDep, SessionDep, get_current_user

router = APIRouter(prefix="/friendships", tags=["friendships"])

logger = logging.getLogger(__name__)


@router.get(
    "/me",
    response_model=DTO[list[UserWithFriendshipInfo]],
)
def get_friends(session: SessionDep, user: SecurityDep) -> dict:
    """Fetch a friends list for a specific friend."""
    user: User = session.get(User, user.id)
    if not user:
        raise ResourceNotFoundError("User", user.id)
    return {"data": user.friends_with_details}


@router.post("/", response_model=DTO[bool])
def create_friend_request(
    friendship_create: FriendshipCreate,
    session: SessionDep,
    user: SecurityDep,
) -> dict:
    """Create a new friend request. The current user is the requester."""
    requester_id = user.id
    addressee_id = friendship_create.addressee_id

    if requester_id == addressee_id:
        raise HTTPException(
            status_code=400, detail="Cannot send a friend request to yourself."
        )

    addressee_user = session.get(User, addressee_id)
    if not addressee_user:
        raise ResourceNotFoundError("user", addressee_id)

    # 3. Check if a friendship (in any order or status) already exists
    #    This uses the LEAST/GREATEST functions to match the unique index logic.
    #    This check helps provide a user-friendly error before hitting DB constraint.
    id_1 = func.least(requester_id, addressee_id)
    id_2 = func.greatest(requester_id, addressee_id)

    stmt_exists = select(Friendships).where(
        and_(
            func.least(Friendships.requester_id, Friendships.addressee_id) == id_1,
            func.greatest(Friendships.requester_id, Friendships.addressee_id) == id_2,
        )
    )
    existing_friendship = session.exec(stmt_exists).first()

    if existing_friendship:
        if existing_friendship.status == FriendshipStatus.PENDING:
            detail_msg = "A friend request is already pending between these users."
        elif existing_friendship.status == FriendshipStatus.ACCEPTED:
            detail_msg = "These users are already friends."
        elif existing_friendship.status == FriendshipStatus.BLOCKED:
            # You might want different behavior/message for blocked status
            detail_msg = "A friendship interaction is blocked between these users."
        else:  # REJECTED or other states
            # If a request was rejected, you might allow a new one.
            # For now, let's treat any existing record as a conflict to simplify.
            # If you want to allow re-request after rejection, remove this branch
            # and the database will handle it or you might update the existing record's status.
            detail_msg = "A previous friendship interaction exists between these users."
        raise HTTPException(status_code=409, detail=detail_msg)  # 409 Conflict

    # 4. Create new friendship record
    #    The 'status' will default to PENDING as per your Friendships model definition.
    new_friendship = Friendships(
        requester_id=requester_id,
        addressee_id=addressee_id,
    )

    session.add(new_friendship)
    try:
        session.commit()
    except Exception as exc:
        session.rollback()

        raise HTTPException(
            status_code=500,
            detail="Could not create friend request due to a database error.",
        ) from exc

    return DTO(data=True)


@router.get(
    "/{user_id}",
    dependencies=[Depends(get_current_user)],
    response_model=DTO[list[FriendshipPublic]],
)
def check_friend_requests(
    user_id: str, request_type: FriendRequestType | None, session: SessionDep
) -> dict:
    """Get incoming or outgoing friend requests based on request_type."""
    user = session.get(User, user_id)
    if not user:
        raise ResourceNotFoundError("User", user_id)

    user_involvement_condition = None

    if request_type == "outgoing":
        user_involvement_condition = Friendships.requester_id == user.id
    elif request_type == "incoming":
        user_involvement_condition = Friendships.addressee_id == user.id
    else:
        # If None check if the current user is either requester or addressee and get all records
        user_involvement_condition = or_(
            Friendships.requester_id == user.id, Friendships.addressee_id == user.id
        )
    query = select(Friendships).where(
        and_(
            user_involvement_condition,
            Friendships.status == FriendshipStatus.PENDING,
        ).options(  # solve N + 1 query problem (sqlalchemy lazy load by defautl)
            selectinload(Friendships.requester),
            selectinload(Friendships.addressee),
        )
    )

    results = session.exec(query).all()

    # Convert Friendships DB models to FriendshipPublic Pydantic models
    friendship_public_list: list[FriendshipPublic] = []
    for fs_db in results:
        try:
            public_model = FriendshipPublic.model_validate(fs_db)
            friendship_public_list.append(public_model)
        except Exception:
            logger.exception(
                "Error converting Friendship DB object %s to Public", fs_db
            )

    return {"data": results}


@router.patch("/{friendship_id}", response_model=DTO[FriendshipPublic])
def respond_to_friend_request(
    session: SessionDep,
    user: SecurityDep,
    friendship_id: str,
    friendship_update: FriendshipUpdate,
) -> dict:
    """Allow the addressee of a friend request to accept or reject it."""
    friendship_to_update = session.get(Friendships, friendship_id)

    if not friendship_to_update:
        raise ResourceNotFoundError("Friendship", friendship_id)

    #    Only the addressee can accept or reject a pending request.
    if friendship_to_update.addressee_id != user.id:
        # This also implicitly covers the case where the requester tries to respond.
        # It also covers cases where a completely unrelated user tries to meddle.
        raise HTTPException(
            status_code=403,  # Forbidden
            detail="You are not authorized to respond to this friend request.",
        )
    # --- END AUTHORIZATION ---

    # State Check: Can only respond to PENDING requests.
    if friendship_to_update.status != FriendshipStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"This friend request is not pending (current status: {friendship_to_update.status.value}).",
        )

    # Validate the new status (user can only set to ACCEPTED or REJECTED here)
    new_status = friendship_update.status
    if new_status not in [FriendshipStatus.ACCEPTED, FriendshipStatus.REJECTED]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status for responding. Must be 'accepted' or 'rejected'.",
        )

    # Update status
    friendship_to_update.status = new_status
    session.add(friendship_to_update)
    session.commit()
    session.refresh(friendship_to_update)

    response_data = FriendshipPublic.model_validate(friendship_to_update)
    return DTO(data=response_data)
