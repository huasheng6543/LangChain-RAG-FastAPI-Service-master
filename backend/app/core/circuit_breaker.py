import pybreaker
from fastapi import Request, HTTPException

from app.db.redis_config import connect_redis
from app.core.logger_handler import logger


class CircuitBreakerMiddleware:
    def __init__(self, app):
        self.app = app
        self.breakers = {}

    def _get_breaker(self, key):
        if key not in self.breakers:
            self.breakers[key] = pybreaker.CircuitBreaker(
                fail_max=5,
                reset_timeout=30,
                exclude=[HTTPException]
            )
        return self.breakers[key]

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        from fastapi import Request
        from starlette.responses import JSONResponse
        
        request = Request(scope, receive)
        path = request.url.path
        
        breaker = self._get_breaker(path)
        
        async def call_app():
            await self.app(scope, receive, send)
        
        try:
            await breaker.call(call_app)
        except pybreaker.CircuitBreakerError:
            logger.warning(f"【熔断】接口 {path} 触发熔断")
            response = JSONResponse(
                {"detail": "服务暂时不可用，请稍后重试"},
                status_code=503
            )
            await response(scope, receive, send)
        except Exception as e:
            logger.error(f"【熔断】接口 {path} 执行失败: {e}")
            raise


def circuit_breaker_decorator(fail_max=5, reset_timeout=30):
    breaker = pybreaker.CircuitBreaker(
        fail_max=fail_max,
        reset_timeout=reset_timeout,
        exclude=[HTTPException]
    )

    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await breaker.call(func, *args, **kwargs)
            except pybreaker.CircuitBreakerError:
                raise HTTPException(
                    status_code=503,
                    detail="服务暂时不可用，请稍后重试"
                )
        return wrapper
    return decorator