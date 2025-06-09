"""FastAPI endpoints for querying and mutating friendship entities."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import and_, func, or_, select

from src.api.deps import SecurityDep, SessionDep, get_current_user
from src.core.exceptions import ResourceNotFoundError
from src.models.models import (
    FriendRequestType,
    FriendshipCreate,
    FriendshipPublic,
    Friendships,
    FriendshipStatus,
    FriendshipUpdate,
    User,
    UserWithFriendshipInfo,
)
from src.models.shared import DTO

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
    friendship_create: FriendshipCreate,  # Assuming addressee_id is uuid.UUID in this model
    session: SessionDep,
    user: SecurityDep,
) -> dict:
    """Create a new friend request. The current user is the requester."""
    # --- Current User ID Conversion (if needed) ---
    current_user_id_str = user.id  # Assuming this is still a string from SecurityDep
    try:
        current_user_uuid: uuid.UUID = uuid.UUID(current_user_id_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid user ID format in security token: {current_user_id_str}",
        ) from exc

    # --- Addressee ID is ALREADY a UUID from Pydantic model ---
    # No conversion needed for friendship_create.addressee_id if it's typed as uuid.UUID in FriendshipCreate
    addressee_uuid: uuid.UUID = friendship_create.addressee_id
    # --- End Addressee ID Handling ---

    if current_user_uuid == addressee_uuid:
        raise HTTPException(
            status_code=400, detail="Cannot send a friend request to yourself."
        )

    addressee_user_object = session.get(User, addressee_uuid)
    if not addressee_user_object:
        # For the error message, you might want to convert the UUID back to string
        # if the client expects a string representation they sent.
        raise ResourceNotFoundError("user", str(addressee_uuid))

    sorted_ids = sorted([current_user_uuid, addressee_uuid])
    param_id1_val: uuid.UUID = sorted_ids[0]
    param_id2_val: uuid.UUID = sorted_ids[1]

    stmt_exists = select(Friendships).where(
        and_(
            func.least(Friendships.requester_id, Friendships.addressee_id)
            == param_id1_val,
            func.greatest(Friendships.requester_id, Friendships.addressee_id)
            == param_id2_val,
        )
    )
    existing_friendship = session.exec(stmt_exists).first()

    if existing_friendship:
        if existing_friendship.status == FriendshipStatus.PENDING:
            detail_msg = "A friend request is already pending between these users."
        elif existing_friendship.status == FriendshipStatus.ACCEPTED:
            detail_msg = "These users are already friends."
        elif existing_friendship.status == FriendshipStatus.BLOCKED:
            detail_msg = "A friendship interaction is blocked between these users."
        else:
            detail_msg = "A previous friendship interaction exists between these users."
        raise HTTPException(status_code=409, detail=detail_msg)

    new_friendship = Friendships(
        requester_id=current_user_uuid,
        addressee_id=addressee_uuid,
    )

    session.add(new_friendship)
    try:
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.exception(
            "Database commit failed when creating friendship. Payload: requester_id=%(requester_id)s, addressee_id=%(addressee_id)s",
            {"requester_id": current_user_uuid, "addressee_id": addressee_uuid},
        )
        logger.exception(
            "Original database error was:"
        )  # This will print the full traceback of 'exc'
        # --- END LOGGING ---

        # Log exc
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
def get_friend_requests(
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
    query = (
        select(Friendships)
        .where(
            and_(
                user_involvement_condition,
                Friendships.status == FriendshipStatus.PENDING,
            )
        )
        .options(  # solve N + 1 query problem (sqlalchemy lazy load by defautl)
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
    if friendship_to_update.addressee_id != uuid.UUID(user.id):
        logger.info(
            "Responding to friendship request: %(addressee_id)s, by user: %(user_id)s",
            {"addressee_id": friendship_to_update.addressee_id, "user_id": user.id},
        )
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


@router.delete("/{friendship_id}", response_model=DTO[bool])
def delete_friendship(
    session: SessionDep, user: SecurityDep, friendship_id: str
) -> dict:
    """Delete friendship record and handle edge cases."""
    friendship_to_delete = session.get(Friendships, friendship_id)
    logger.warning("Deleting friendship with id %s", friendship_id)
    if not friendship_to_delete:
        raise ResourceNotFoundError("friendship", friendship_id)
    if uuid.UUID(user.id) not in (
        friendship_to_delete.addressee_id,
        friendship_to_delete.requester_id,
    ):
        logger.critical("User ID: %s", user.id)
        raise HTTPException(
            status_code=403, detail="Error user is not part of friendship"
        )
    if friendship_to_delete.status == FriendshipStatus.PENDING:
        logger.warning(
            "User is trying to delete a friendship that is still in pending state"
        )
    session.delete(friendship_to_delete)
    session.commit()
    return {"data": True}
