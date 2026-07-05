import logging
import os
import time
from datetime import datetime
import sys

project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

logs_dir = os.path.join(project_path, 'logs')
os.makedirs(logs_dir, exist_ok=True)

DEFAULT_LOGGING_FORMAT = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

ACCESS_LOG_FORMAT = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(client_ip)s - %(method)s - %(path)s - %(status_code)s - %(duration)sms - %(user_id)s - %(session_id)s'
)


class AccessLogFilter(logging.Filter):
    def filter(self, record):
        record.client_ip = getattr(record, 'client_ip', '-')
        record.method = getattr(record, 'method', '-')
        record.path = getattr(record, 'path', '-')
        record.status_code = getattr(record, 'status_code', '-')
        record.duration = getattr(record, 'duration', '-')
        record.user_id = getattr(record, 'user_id', '-')
        record.session_id = getattr(record, 'session_id', '-')
        return True


def get_logger(
        name: str = "agent",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        log_file: str = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(DEFAULT_LOGGING_FORMAT)
    logger.addHandler(console_handler)

    if log_file is None:
        log_file = f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    
    logs_dir = os.path.join(project_path, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    file_handler = logging.FileHandler(os.path.join(logs_dir, log_file), encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOGGING_FORMAT)
    logger.addHandler(file_handler)

    return logger


def get_access_logger() -> logging.Logger:
    logger = logging.getLogger("access")
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ACCESS_LOG_FORMAT)
    console_handler.addFilter(AccessLogFilter())
    logger.addHandler(console_handler)
    
    log_file = f"access_{datetime.now().strftime('%Y%m%d')}.log"
    logs_dir = os.path.join(project_path, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    file_handler = logging.FileHandler(os.path.join(logs_dir, log_file), encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(ACCESS_LOG_FORMAT)
    file_handler.addFilter(AccessLogFilter())
    logger.addHandler(file_handler)
    
    return logger


logger = get_logger()
access_logger = get_access_logger()


class RequestLogMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        from fastapi import Request
        
        request = Request(scope, receive)
        start_time = time.time()
        
        client_ip = request.client.host
        if not client_ip:
            client_ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or '-'
        
        method = request.method
        path = request.url.path
        
        user_id = '-'
        session_id = '-'
        
        authorization = request.headers.get('Authorization', '')
        if authorization.startswith('Bearer '):
            try:
                from jose import jwt
                import os
                token = authorization[7:]
                payload = jwt.decode(token, os.getenv('SECRET_KEY', ''), algorithms=['HS256'], options={'verify_signature': False})
                user_id = payload.get('user_id', '-')
            except:
                pass
        
        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                status_code = message['status']
                duration = int((time.time() - start_time) * 1000)
                
                access_logger.info(
                    f"Request: {method} {path}",
                    extra={
                        'client_ip': client_ip,
                        'method': method,
                        'path': path,
                        'status_code': status_code,
                        'duration': duration,
                        'user_id': user_id,
                        'session_id': session_id
                    }
                )
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


if __name__ == '__main__':
    logger = get_logger(log_file='test.log')
    print(f"项目根目录: {project_path}")
    print(f"日志目录: {logs_dir}")
    logger.info('这是一条info日志')
    logger.debug('这是一条debug日志')
    logger.error('这是一条error日志')
    logger.warning('这是一条warning日志')
    print("日志测试完成，请检查logs目录是否创建")