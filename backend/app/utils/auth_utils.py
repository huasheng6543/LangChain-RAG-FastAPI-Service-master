import os
import jwt
import uuid
import redis
import aiomysql
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.chat_history import User

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

import bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))


async def connect_redis():
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True
        )
        return redis_client
    except Exception as e:
        return None


async def set_redis_cache(key: str, value: dict, expire: int = 3600):
    redis_client = await connect_redis()
    if redis_client:
        try:
            import json
            await asyncio.to_thread(redis_client.setex, key, expire, json.dumps(value))
        except Exception as e:
            pass


async def get_user(username: str) -> Optional[User]:
    async with aiomysql.create_pool(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        db=os.getenv('MYSQL_DATABASE', 'chat_history'),
        charset='utf8mb4'
    ) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM users WHERE username = %s OR email = %s",
                    (username, username)
                )
                row = await cur.fetchone()
                if row:
                    return User(**row)
                return None


async def authenticate_user(username: str, password: str) -> Optional[User]:
    user = await get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        user = await get_user(payload.get("sub"))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_user_info_from_redis(user_id: str, credentials: HTTPAuthorizationCredentials):
    redis_client = await connect_redis()
    key = f"user:{user_id}"
    
    try:
        user_info = await asyncio.to_thread(redis_client.get, key) if redis_client else None
        if user_info is None:
            async with aiomysql.create_pool(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                port=int(os.getenv('MYSQL_PORT', '3306')),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', ''),
                db=os.getenv('MYSQL_DATABASE', 'chat_history'),
                charset='utf8mb4'
            ) as pool:
                async with pool.acquire() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cur:
                        await cur.execute(
                            "SELECT id, username, email, role FROM users WHERE id = %s",
                            (user_id,)
                        )
                        row = await cur.fetchone()
                        if row:
                            user_data = {
                                "id": row['id'],
                                "username": row['username'],
                                "email": row['email'],
                                "role": row['role']
                            }
                            await set_redis_cache(key, user_data, expire=3600)
                            user_info = user_data
        else:
            import json
            try:
                user_info = json.loads(user_info)
            except json.JSONDecodeError:
                await asyncio.to_thread(redis_client.delete, key) if redis_client else None
                return None
    except Exception as e:
        user_info = None

    return user_info


async def create_user(username: str, email: str, password: str) -> User:
    hashed_password = get_password_hash(password)
    user_id = str(uuid.uuid4())
    
    async with aiomysql.create_pool(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        db=os.getenv('MYSQL_DATABASE', 'chat_history'),
        charset='utf8mb4'
    ) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (id, username, email, hashed_password, role, is_active) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, username, email, hashed_password, "user", True)
                )
                await conn.commit()
    
    return User(
        id=user_id,
        username=username,
        email=email,
        hashed_password=hashed_password,
        role="user",
        is_active=True
    )


def decode_django_jwt(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False})
        return payload
    except jwt.PyJWTError:
        return None