# 1. Import the modules that define your classes
from . import (
    friendship,  # This loads friendship.py
    user,  # This loads user.py
)

# ... import any other model files (e.g., car, trip)

# 2. Now that all model modules are imported, resolve forward references

# Create a dictionary of all relevant global/module namespaces
# This helps Pydantic find types defined in other modules.
update_refs_namespaces = {
    # **sys.modules[__name__].__dict__, # Namespace of models/__init__.py (usually not needed for resolving types within other modules)
    **user.__dict__,  # Everything defined in user.py (IMPORTANT: this is where User is)
    **friendship.__dict__,  # Everything defined in friendship.py
    # Add other modules if they define types needed by forward refs in user/friendship
    # For example, if UserPublic needed "CarPublic" from a car.py:
    # **car.__dict__,
}
# If your models/car.py or models/trip.py define Pydantic models that User/Friendship
# models refer to via string, add them to update_refs_namespaces too.


# For Pydantic v2
if hasattr(friendship, "FriendshipPublic"):
    print(
        f"Rebuilding FriendshipPublic. 'User' in user.__dict__: {'User' in user.__dict__}"
    )
    print(
        f"Namespaces being passed: {list(update_refs_namespaces.keys())[:20]}..."
    )  # Print some keys
    try:
        friendship.FriendshipPublic.model_rebuild(
            _types_namespace=update_refs_namespaces,  # <--- USE THIS
            force=True,
        )
        print("FriendshipPublic rebuilt successfully.")
    except Exception as e:  # Catch generic Exception to see if it's still NameError
        print(f"Error rebuilding FriendshipPublic: {type(e).__name__}: {e}")
        # If it's still NameError, print the namespace keys Pydantic might be using internally
        # if isinstance(e, NameError):
        #     # This is trickier as the direct evaluation scope is deep inside Pydantic
        #     pass
        raise

# If UserPublic (in user.py) needs FriendshipPublic (in friendship.py)
if hasattr(user, "UserPublic") and hasattr(
    user.UserPublic, "model_fields"
):  # Check it's a Pydantic model
    # And if UserPublic actually uses "FriendshipPublic" or other forward refs
    # you'd check its annotations for string types. For now, let's assume it might.
    print(
        f"Rebuilding UserPublic. 'FriendshipPublic' in friendship.__dict__: {'FriendshipPublic' in friendship.__dict__}"
    )
    try:
        user.UserPublic.model_rebuild(
            _types_namespace=update_refs_namespaces,  # <--- USE THIS
            force=True,
        )
        print("UserPublic rebuilt successfully.")
    except Exception as e:
        print(f"Error rebuilding UserPublic: {type(e).__name__}: {e}")
        raise

# Also, ensure SQLModel relationships are resolved if they weren't automatically
# SQLModel itself usually handles its own forward references well after all modules are imported.
# This is mainly for Pydantic models.

# 3. Optionally expose key items for easier imports elsewhere
from .friendship import (
    FriendshipCreate,
    FriendshipPublic,
    Friendships,
    FriendshipStatus,
    FriendshipUpdate,
)
from .user import RiderType, User, UserPublic, UserUpdate  # Add whatever you need
# from .car import Car, CarPublic ... etc.
