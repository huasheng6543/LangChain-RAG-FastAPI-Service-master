import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

print("=" * 70)
print("环境配置验证脚本")
print("=" * 70)

errors = []
warnings = []


def check_env_var(name, expected_type=str, required=True, desc=""):
    value = os.getenv(name)
    if required and value is None:
        errors.append(f"❌ 缺少必要环境变量: {name} ({desc})")
        return None
    if value is None:
        warnings.append(f"⚠️  可选环境变量未设置: {name} ({desc})")
        return None
    try:
        if expected_type == int:
            return int(value)
        elif expected_type == float:
            return float(value)
        elif expected_type == bool:
            return value.lower() == "true"
        return value
    except ValueError:
        errors.append(f"❌ 环境变量类型错误: {name}={value} 应为 {expected_type.__name__}")
        return None


print("\n【1】基础配置检查")
print("-" * 50)
secret_key = check_env_var("SECRET_KEY", desc="JWT密钥")
algorithm = check_env_var("ALGORITHM", desc="JWT算法")
access_token_expire = check_env_var("ACCESS_TOKEN_EXPIRE_MINUTES", int, desc="Token过期时间(分钟)")

print(f"  SECRET_KEY: {'已设置' if secret_key else '未设置'}")
print(f"  ALGORITHM: {algorithm}")
print(f"  ACCESS_TOKEN_EXPIRE_MINUTES: {access_token_expire}")

print("\n【2】MySQL配置检查")
print("-" * 50)
mysql_user = check_env_var("MYSQL_USER", desc="数据库用户名")
mysql_password = check_env_var("MYSQL_PASSWORD", desc="数据库密码")
mysql_host = check_env_var("MYSQL_HOST", desc="数据库地址")
mysql_port = check_env_var("MYSQL_PORT", int, desc="数据库端口")
mysql_db = check_env_var("MYSQL_DATABASE", desc="数据库名")

print(f"  MYSQL_USER: {mysql_user}")
print(f"  MYSQL_PASSWORD: {'已设置' if mysql_password else '未设置'}")
print(f"  MYSQL_HOST: {mysql_host}")
print(f"  MYSQL_PORT: {mysql_port}")
print(f"  MYSQL_DATABASE: {mysql_db}")

print("\n【3】Redis配置检查")
print("-" * 50)
redis_host = check_env_var("REDIS_HOST", desc="Redis地址")
redis_port = check_env_var("REDIS_PORT", int, desc="Redis端口")
redis_db = check_env_var("REDIS_DB", int, desc="Redis数据库编号")

print(f"  REDIS_HOST: {redis_host}")
print(f"  REDIS_PORT: {redis_port}")
print(f"  REDIS_DB: {redis_db}")

print("\n【4】Milvus配置检查")
print("-" * 50)
milvus_host = check_env_var("MILVUS_HOST", required=False, desc="Milvus地址")
milvus_port = check_env_var("MILVUS_PORT", required=False, desc="Milvus端口")
use_milvus = check_env_var("USE_MILVUS", bool, required=False, desc="是否使用Milvus")

print(f"  MILVUS_HOST: {milvus_host or 'localhost'}")
print(f"  MILVUS_PORT: {milvus_port or '19530'}")
print(f"  USE_MILVUS: {'是' if use_milvus else '否'}")

print("\n【5】vLLM配置检查")
print("-" * 50)
vllm_model_name = check_env_var("VLLM_MODEL_NAME", required=False, desc="模型名称")
vllm_model_path = check_env_var("VLLM_MODEL_PATH", required=False, desc="模型路径")
vllm_gpu_util = check_env_var("VLLM_GPU_MEMORY_UTILIZATION", float, required=False, desc="GPU显存利用率")
vllm_max_len = check_env_var("VLLM_MAX_MODEL_LEN", int, required=False, desc="最大上下文长度")
vllm_enforce_eager = check_env_var("VLLM_ENFORCE_EAGER", bool, required=False, desc="是否强制eager模式")
vllm_quantization = check_env_var("VLLM_QUANTIZATION", required=False, desc="量化类型")

print(f"  VLLM_MODEL_NAME: {vllm_model_name or 'Qwen/Qwen3-7B-Instruct-AWQ'}")
print(f"  VLLM_MODEL_PATH: {vllm_model_path or './models/Qwen3-7B-Instruct-AWQ'}")
print(f"  VLLM_GPU_MEMORY_UTILIZATION: {vllm_gpu_util or 0.90}")
print(f"  VLLM_MAX_MODEL_LEN: {vllm_max_len or 8192}")
print(f"  VLLM_ENFORCE_EAGER: {'是' if vllm_enforce_eager else '否'}")
print(f"  VLLM_QUANTIZATION: {vllm_quantization or 'AWQ'}")

print("\n【6】模型路径配置检查")
print("-" * 50)
reranker_model_path = check_env_var("RERANKER_MODEL_PATH", required=False, desc="重排序模型路径")

print(f"  RERANKER_MODEL_PATH: {reranker_model_path}")

if reranker_model_path and not os.path.exists(reranker_model_path):
    warnings.append(f"⚠️  重排序模型路径不存在: {reranker_model_path}")

print("\n【7】依赖包检查")
print("-" * 50)

required_deps = {
    "fastapi": "fastapi",
    "sqlalchemy": "sqlalchemy",
    "python-dotenv": "dotenv",
    "aiofiles": "aiofiles",
    "pydantic": "pydantic",
    "python-jose": "jose",
    "passlib": "passlib",
    "aiomysql": "aiomysql",
    "redis": "redis",
    "pymilvus": "pymilvus",
    "celery": "celery",
    "pybreaker": "pybreaker",
    "langchain-core": "langchain_core",
    "langchain-community": "langchain_community",
    "sentence-transformers": "sentence_transformers",
    "rank_bm25": "rank_bm25"
}

missing_deps = []
for dep_name, import_name in required_deps.items():
    try:
        __import__(import_name)
        print(f"  ✅ {dep_name}")
    except ImportError:
        missing_deps.append(dep_name)
        print(f"  ❌ {dep_name}")

if missing_deps:
    errors.append(f"❌ 缺少依赖包: {', '.join(missing_deps)}")

print("\n【8】配置文件检查")
print("-" * 50)
config_files = [
    "app/config/chroma.yaml",
    "app/config/rag.yaml",
    "app/config/prompt.yaml",
    "app/config/agent.yaml",
    "app/db/db_config.py",
    "app/db/redis_config.py",
    "app/core/rate_limit.py",
    "app/core/circuit_breaker.py",
    "app/core/logger_handler.py",
    "app/core/permission.py",
    "app/llm/vllm_adapter.py",
    "app/rag/milvus_store.py",
    "app/rag/vector_store.py",
    "app/rag/reorder_service.py",
    "app/rag/rag_service.py",
    "app/celery_config.py",
    "app/tasks/document_tasks.py",
    "main.py",
]

for config_file in config_files:
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)
    if os.path.exists(full_path):
        print(f"  ✅ {config_file}")
    else:
        errors.append(f"❌ 配置文件不存在: {config_file}")
        print(f"  ❌ {config_file}")

print("\n" + "=" * 70)
if errors:
    print("❌ 检查发现错误:")
    for error in errors:
        print(f"  {error}")
    print("\n请修复以上错误后再启动服务。")
    sys.exit(1)
else:
    print("✅ 所有配置检查通过！")
    
if warnings:
    print("\n⚠️  警告信息:")
    for warning in warnings:
        print(f"  {warning}")
    print("\n建议修复警告后再启动服务。")

print("\n启动命令参考:")
print("  开发环境: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
print("  Celery任务: celery -A app.celery_config worker --loglevel=info")
print("  Docker部署: docker-compose up -d")
