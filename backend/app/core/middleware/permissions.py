"""require_permission decorator — fine-grained RBAC enforcement.

Usage:
    @router.get("/devices")
    @require_permission("asset:device:list")
    async def list_devices(...): ...
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Depends

from app.core.exceptions import ForbiddenError
from app.core.middleware.auth import get_current_user
from app.modules.module9_platform.permission_registry import BUILTIN_ROLES, PERMISSION_DEFINITIONS


def _expand_permissions(perm_set: set[str]) -> set[str]:
    """Expand wildcard permissions like 'asset:*:*' to all matching codes."""
    expanded = set(perm_set)
    for perm in list(perm_set):
        parts = perm.split(":")
        if parts == ["*", "*", "*"]:
            return set(PERMISSION_DEFINITIONS.keys())  # superadmin
        if len(parts) == 3:
            if parts[1] == "*" and parts[2] == "*":
                expanded.update(p for p in PERMISSION_DEFINITIONS if p.startswith(f"{parts[0]}:"))
            elif parts[2] == "*":
                expanded.update(p for p in PERMISSION_DEFINITIONS if p.startswith(f"{parts[0]}:{parts[1]}:"))
    return expanded


def _get_user_permissions(user: dict) -> set[str]:
    """Resolve user's effective permission set from their role."""
    role = user.get("role", "viewer")
    role_def = BUILTIN_ROLES.get(role, BUILTIN_ROLES["viewer"])
    return _expand_permissions(role_def["permissions"])


def require_permission(permission_code: str) -> Callable:
    """Decorator: require a specific permission code on the endpoint.

    Must be used AFTER @router.get/post/etc. decorators.
    The handler must receive `current_user: dict = Depends(get_current_user)`.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):
            # Find the current_user in kwargs (injected by Depends)
            user = kwargs.get("current_user")
            if not user:
                # Try to get from args
                for arg in args:
                    if isinstance(arg, dict) and "user_id" in arg and "role" in arg:
                        user = arg
                        break
            if not user:
                raise ForbiddenError("Authentication required")

            perms = _get_user_permissions(user)
            if permission_code not in perms:
                raise ForbiddenError(
                    f"Permission denied: requires '{permission_code}'"
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def has_permission(user: dict, permission_code: str) -> bool:
    """Check if a user has a specific permission (for use in service layer)."""
    perms = _get_user_permissions(user)
    return permission_code in perms


def get_effective_permissions(user: dict) -> set[str]:
    """Get all effective permissions for a user."""
    return _get_user_permissions(user)
