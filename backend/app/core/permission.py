from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.db.db_config import get_db
from app.models.chat_history import User
from app.utils.auth_utils import get_current_user, security


class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {self.allowed_roles}"
            )
        return user


def require_admin(user: User = Depends(RoleChecker(["admin"]))):
    return user


def require_user(user: User = Depends(RoleChecker(["user", "admin"]))):
    return user


def require_role(roles: list):
    return RoleChecker(roles)