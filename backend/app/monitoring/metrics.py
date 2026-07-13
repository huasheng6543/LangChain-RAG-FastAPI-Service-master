from prometheus_client import Counter, Gauge, Histogram, Summary
from datetime import datetime
import time

REQUEST_COUNT = Counter(
    "fastapi_requests_total",
    "Total number of requests received",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "fastapi_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"]
)

ACTIVE_CONNECTIONS = Gauge(
    "fastapi_active_connections",
    "Number of active connections"
)

CHAT_REQUEST_COUNT = Counter(
    "rag_chat_requests_total",
    "Total number of chat requests",
    ["status"]
)

CHAT_REQUEST_LATENCY = Histogram(
    "rag_chat_request_latency_seconds",
    "Chat request latency in seconds"
)

DOCUMENT_RETRIEVAL_COUNT = Counter(
    "rag_document_retrieval_total",
    "Total number of document retrieval operations",
    ["status"]
)

DOCUMENT_RETRIEVAL_LATENCY = Histogram(
    "rag_document_retrieval_latency_seconds",
    "Document retrieval latency in seconds"
)

DOCUMENT_REORDER_COUNT = Counter(
    "rag_document_reorder_total",
    "Total number of document reorder operations",
    ["status"]
)

DOCUMENT_REORDER_LATENCY = Histogram(
    "rag_document_reorder_latency_seconds",
    "Document reorder latency in seconds"
)

LLM_CALL_COUNT = Counter(
    "rag_llm_calls_total",
    "Total number of LLM calls",
    ["model_type", "status"]
)

LLM_CALL_LATENCY = Histogram(
    "rag_llm_call_latency_seconds",
    "LLM call latency in seconds",
    ["model_type"]
)

ERROR_COUNT = Counter(
    "fastapi_errors_total",
    "Total number of errors",
    ["error_type", "endpoint"]
)

MEMORY_USAGE = Gauge(
    "system_memory_usage_percent",
    "System memory usage percentage"
)

CPU_USAGE = Gauge(
    "system_cpu_usage_percent",
    "System CPU usage percentage"
)

DISK_USAGE = Gauge(
    "system_disk_usage_percent",
    "System disk usage percentage"
)

VECTOR_DB_QUERY_COUNT = Counter(
    "vector_db_queries_total",
    "Total number of vector database queries",
    ["db_type", "status"]
)

VECTOR_DB_QUERY_LATENCY = Histogram(
    "vector_db_query_latency_seconds",
    "Vector database query latency",
    ["db_type"]
)

REDIS_OPERATION_COUNT = Counter(
    "redis_operations_total",
    "Total number of Redis operations",
    ["operation", "status"]
)

REDIS_OPERATION_LATENCY = Histogram(
    "redis_operation_latency_seconds",
    "Redis operation latency",
    ["operation"]
)

MODEL_LOAD_STATUS = Gauge(
    "model_load_status",
    "Model load status (1=loaded, 0=not loaded)",
    ["model_name"]
)

CACHE_HIT_RATE = Summary(
    "cache_hit_rate",
    "Cache hit rate"
)

REQUESTS_PER_MINUTE = Counter(
    "fastapi_requests_per_minute",
    "Requests per minute"
)

START_TIME = Gauge(
    "fastapi_start_time",
    "Application start time"
)

START_TIME.set(time.time())

def record_request(method: str, endpoint: str, status_code: int, latency: float):
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)

def record_chat_request(status: str, latency: float = None):
    CHAT_REQUEST_COUNT.labels(status=status).inc()
    if latency:
        CHAT_REQUEST_LATENCY.observe(latency)

def record_document_retrieval(status: str, latency: float = None):
    DOCUMENT_RETRIEVAL_COUNT.labels(status=status).inc()
    if latency:
        DOCUMENT_RETRIEVAL_LATENCY.observe(latency)

def record_document_reorder(status: str, latency: float = None):
    DOCUMENT_REORDER_COUNT.labels(status=status).inc()
    if latency:
        DOCUMENT_REORDER_LATENCY.observe(latency)

def record_llm_call(model_type: str, status: str, latency: float = None):
    LLM_CALL_COUNT.labels(model_type=model_type, status=status).inc()
    if latency:
        LLM_CALL_LATENCY.labels(model_type=model_type).observe(latency)

def record_error(error_type: str, endpoint: str):
    ERROR_COUNT.labels(error_type=error_type, endpoint=endpoint).inc()

def record_vector_db_query(db_type: str, status: str, latency: float = None):
    VECTOR_DB_QUERY_COUNT.labels(db_type=db_type, status=status).inc()
    if latency:
        VECTOR_DB_QUERY_LATENCY.labels(db_type=db_type).observe(latency)

def record_redis_operation(operation: str, status: str, latency: float = None):
    REDIS_OPERATION_COUNT.labels(operation=operation, status=status).inc()
    if latency:
        REDIS_OPERATION_LATENCY.labels(operation=operation).observe(latency)
