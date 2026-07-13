from fastapi import APIRouter, Depends
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import psutil
import time

from app.monitoring.metrics import (
    MEMORY_USAGE,
    CPU_USAGE,
    DISK_USAGE,
    ACTIVE_CONNECTIONS,
    START_TIME,
)

monitoring_router = APIRouter(prefix="/monitoring", tags=["监控"])

@monitoring_router.get("/metrics")
async def metrics():
    MEMORY_USAGE.set(psutil.virtual_memory().percent)
    CPU_USAGE.set(psutil.cpu_percent())
    DISK_USAGE.set(psutil.disk_usage('/').percent)
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@monitoring_router.get("/health")
async def health():
    uptime = time.time() - START_TIME._value.get()
    
    return {
        "status": "healthy",
        "uptime": round(uptime, 2),
        "memory_usage": f"{MEMORY_USAGE._value.get():.2f}%",
        "cpu_usage": f"{CPU_USAGE._value.get():.2f}%",
        "disk_usage": f"{DISK_USAGE._value.get():.2f}%"
    }

@monitoring_router.get("/system-info")
async def system_info():
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent()
    disk = psutil.disk_usage('/')
    network = psutil.net_io_counters()
    
    return {
        "memory": {
            "total": f"{memory.total / (1024 ** 3):.2f} GB",
            "available": f"{memory.available / (1024 ** 3):.2f} GB",
            "used": f"{memory.used / (1024 ** 3):.2f} GB",
            "percent": f"{memory.percent:.2f}%"
        },
        "cpu": {
            "usage": f"{cpu:.2f}%",
            "cores": psutil.cpu_count(),
            "frequency": f"{psutil.cpu_freq().current:.2f} MHz"
        },
        "disk": {
            "total": f"{disk.total / (1024 ** 3):.2f} GB",
            "used": f"{disk.used / (1024 ** 3):.2f} GB",
            "free": f"{disk.free / (1024 ** 3):.2f} GB",
            "percent": f"{disk.percent:.2f}%"
        },
        "network": {
            "bytes_sent": f"{network.bytes_sent / (1024 ** 2):.2f} MB",
            "bytes_recv": f"{network.bytes_recv / (1024 ** 2):.2f} MB",
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        },
        "uptime": f"{(time.time() - START_TIME._value.get()) / 3600:.2f} hours"
    }

@monitoring_router.get("/metrics/summary")
async def metrics_summary():
    from app.monitoring.metrics import (
        REQUEST_COUNT,
        CHAT_REQUEST_COUNT,
        ERROR_COUNT,
        CHAT_REQUEST_LATENCY,
        DOCUMENT_RETRIEVAL_LATENCY,
        LLM_CALL_LATENCY,
    )
    
    request_count = REQUEST_COUNT._value.get() if hasattr(REQUEST_COUNT, '_value') else 0
    chat_count = CHAT_REQUEST_COUNT._value.get() if hasattr(CHAT_REQUEST_COUNT, '_value') else 0
    error_count = ERROR_COUNT._value.get() if hasattr(ERROR_COUNT, '_value') else 0
    
    return {
        "request_count": request_count,
        "chat_request_count": chat_count,
        "error_count": error_count,
        "system_metrics": {
            "memory_usage": f"{MEMORY_USAGE._value.get():.2f}%",
            "cpu_usage": f"{CPU_USAGE._value.get():.2f}%",
            "disk_usage": f"{DISK_USAGE._value.get():.2f}%"
        },
        "latency_metrics": {
            "chat_request": "monitored",
            "document_retrieval": "monitored",
            "llm_call": "monitored"
        }
    }
