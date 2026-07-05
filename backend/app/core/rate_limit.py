import time
from fastapi import Request, HTTPException

from app.db.redis_config import connect_redis


def rate_limit(limit: int = 1, window: int = 60):
    """
    滑动窗口限流依赖函数
    :param limit: 时间窗口内的最大请求数
    :param window: 时间窗口大小（秒）
    :return: 依赖函数
    """
    async def dependency(request: Request):
        client_ip = request.client.host
        if not client_ip:
            client_ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or 'unknown'

        key = f"rate_limit:aichat:{client_ip}"
        redis = await connect_redis()
        
        if redis is None:
            return
        
        current_time = int(time.time())
        window_start = current_time - window

        await redis.zremrangebyscore(key, 0, window_start)
        
        count = await redis.zcard(key)
        
        if count >= limit:
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试"
            )

        await redis.zadd(key, {current_time: current_time})
        await redis.expire(key, window)

    return dependency


class RateLimitMiddleware:
    """
    全局滑动窗口限流中间件
    """
    def __init__(self, app, limit: int = 100, window: int = 60):
        self.app = app
        self.limit = limit
        self.window = window

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        from fastapi import Request
        request = Request(scope, receive)
        
        client_ip = request.client.host
        if not client_ip:
            client_ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or 'unknown'

        key = f"rate_limit:global:{client_ip}"
        redis = await connect_redis()
        
        if redis is None:
            await self.app(scope, receive, send)
            return
        
        current_time = int(time.time())
        window_start = current_time - self.window

        await redis.zremrangebyscore(key, 0, window_start)
        
        count = await redis.zcard(key)
        
        if count >= self.limit:
            from starlette.responses import JSONResponse
            response = JSONResponse(
                {"detail": "请求过于频繁，请稍后再试"},
                status_code=429
            )
            await response(scope, receive, send)
            return

        await redis.zadd(key, {current_time: current_time})
        await redis.expire(key, self.window)

        await self.app(scope, receive, send)