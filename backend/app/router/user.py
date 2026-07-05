from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from app.core.success_response import success_response
from app.utils.auth_utils import (
    get_current_user_id,
    get_user_info_from_redis,
    security,
    authenticate_user,
    create_access_token,
    create_user,
    get_user
)

user_router = APIRouter(tags=["user"], prefix="/user")


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@user_router.post("/register/")
async def register_user(request: RegisterRequest):
    """用户注册"""
    try:
        user = await create_user(request.username, request.email, request.password)
        
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role}
        )
        
        return success_response(
            message="注册成功",
            data={
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "access_token": access_token
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"注册失败: {str(e)}"
        )


@user_router.post("/login/")
async def login_user(request: LoginRequest):
    """用户登录"""
    user = await authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )
    
    return success_response(
        message="登录成功",
        data={
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "access_token": access_token
        },
    )


@user_router.get("/detail/")
async def get_user_info(user_id: str = Depends(get_current_user_id), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取用户信息"""
    user_info = await get_user_info_from_redis(user_id, credentials)
    return success_response(
        message="获取用户信息成功",
        data=user_info,
    )