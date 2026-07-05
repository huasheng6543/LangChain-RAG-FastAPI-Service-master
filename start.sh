#!/bin/bash
set -e

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BACKEND_DIR="${PROJECT_DIR}/backend"
PYTHON_EXE="python3"
REDIS_PORT=6379
MYSQL_PORT=3306
MILVUS_PORT=19530
FASTAPI_PORT=8000

echo "================================================"
echo "    RAG 后端微服务工程化底座 - 一键启动脚本"
echo "================================================"
echo ""
echo "启动模式:"
echo "  1 - 单向量化模式 (文档上传/向量化/异步任务, 关闭 vLLM)"
echo "  2 - 单 LLM 问答模式 (RAG检索+LLM推理, 关闭 Milvus/Celery)"
echo "  3 - 全链路模式 (全套服务同时运行, 短时测试)"
echo ""

read -p "请输入启动模式 (1/2/3): " MODE

case ${MODE} in
    1)
        echo ""
        echo "================================================"
        echo "    模式1: 单向量化模式"
        echo "================================================"
        echo "启动服务: Redis + MySQL + Celery + FastAPI"
        echo "关闭服务: vLLM + Milvus"
        echo "================================================"
        echo ""
        ;;
    2)
        echo ""
        echo "================================================"
        echo "    模式2: 单 LLM 问答模式"
        echo "================================================"
        echo "启动服务: Redis + MySQL + FastAPI (+ vLLM)"
        echo "关闭服务: Milvus + Celery"
        echo "================================================"
        echo ""
        ENABLE_VLLM=true
        ;;
    3)
        echo ""
        echo "================================================"
        echo "    模式3: 全链路模式"
        echo "================================================"
        echo "启动服务: Redis + MySQL + Milvus + Celery + FastAPI (+ vLLM)"
        echo "================================================"
        echo ""
        ENABLE_VLLM=true
        ENABLE_MILVUS=true
        ENABLE_CELERY=true
        ;;
    *)
        echo "无效的模式选择!"
        exit 1
        ;;
esac

echo "[1/5] 检查 Python 环境..."
if ! command -v ${PYTHON_EXE} &> /dev/null; then
    echo "  ERROR: 未找到 Python，请安装 Python 3.10+"
    exit 1
fi
echo "  OK: Python 环境正常"

echo ""
echo "[2/5] 检查项目目录..."
if [ ! -d "${BACKEND_DIR}" ]; then
    echo "  ERROR: 后端目录不存在: ${BACKEND_DIR}"
    exit 1
fi
echo "  OK: 项目目录正常"

echo ""
echo "[3/5] 检查环境配置..."
if [ ! -f "${BACKEND_DIR}/.env" ]; then
    echo "  ERROR: 环境配置文件不存在: ${BACKEND_DIR}/.env"
    exit 1
fi
echo "  OK: 环境配置正常"

echo ""
echo "[4/5] 检查依赖包..."
cd "${BACKEND_DIR}"
${PYTHON_EXE} verify_env.py || {
    echo "  ERROR: 依赖包检查失败，请安装缺失的依赖"
    exit 1
}
echo "  OK: 依赖包检查通过"

echo ""
echo "[5/5] 启动服务..."

echo ""
echo "--- 启动 Redis ---"
if lsof -Pi :${REDIS_PORT} -sTCP:LISTEN -t >/dev/null; then
    echo "  WARN: 端口 ${REDIS_PORT} 已被占用，跳过启动 Redis"
else
    redis-server --daemonize yes
    sleep 3
    echo "  OK: Redis 启动成功"
fi

echo ""
echo "--- 启动 MySQL ---"
if lsof -Pi :${MYSQL_PORT} -sTCP:LISTEN -t >/dev/null; then
    echo "  WARN: 端口 ${MYSQL_PORT} 已被占用，跳过启动 MySQL"
else
    echo "  INFO: MySQL 需要手动启动，请确认 MySQL 服务已运行"
fi

if [ "${ENABLE_MILVUS}" = "true" ]; then
    echo ""
    echo "--- 启动 Milvus ---"
    if lsof -Pi :${MILVUS_PORT} -sTCP:LISTEN -t >/dev/null; then
        echo "  WARN: 端口 ${MILVUS_PORT} 已被占用，跳过启动 Milvus"
    else
        echo "  INFO: 正在启动 Milvus..."
        docker start rag-milvus 2>/dev/null || docker run -d --name rag-milvus -p 19530:19530 -p 9091:9091 milvusdb/milvus:v2.4.5
        sleep 10
        echo "  OK: Milvus 启动成功"
    fi
fi

if [ "${ENABLE_CELERY}" = "true" ]; then
    echo ""
    echo "--- 启动 Celery ---"
    cd "${BACKEND_DIR}"
    nohup celery -A app.celery_config worker --loglevel=info > celery.log 2>&1 &
    sleep 3
    echo "  OK: Celery 启动成功"
fi

echo ""
echo "--- 启动 FastAPI ---"
cd "${BACKEND_DIR}"

if [ "${ENABLE_VLLM}" = "true" ]; then
    echo "  INFO: 启用 vLLM 本地大模型模式"
    export VLLM_ENABLED=true
else
    echo "  INFO: 关闭 vLLM，使用云端模型"
    export VLLM_ENABLED=false
fi

nohup ${PYTHON_EXE} -m uvicorn main:app --host 0.0.0.0 --port ${FASTAPI_PORT} > fastapi.log 2>&1 &
sleep 5

echo ""
echo "================================================"
echo "    服务启动完成!"
echo "================================================"
echo ""
echo "服务地址:"
echo "  FastAPI: http://localhost:${FASTAPI_PORT}"
echo "  API文档: http://localhost:${FASTAPI_PORT}/docs"
echo ""
echo "模式说明:"
case ${MODE} in
    1)
        echo "  当前模式: 单向量化模式"
        echo "  可用功能: 文档上传、向量化、异步任务"
        echo "  不可用: LLM问答推理、Milvus向量库"
        ;;
    2)
        echo "  当前模式: 单 LLM 问答模式"
        echo "  可用功能: RAG检索、LLM问答推理"
        echo "  不可用: Milvus向量库、Celery异步任务"
        ;;
    3)
        echo "  当前模式: 全链路模式"
        echo "  可用功能: 全部功能"
        ;;
esac
echo ""
echo "健康检查:"
${PYTHON_EXE} -c "import urllib.request; print(urllib.request.urlopen('http://localhost:${FASTAPI_PORT}/health').read().decode())" 2>/dev/null || echo "  WARN: 健康检查失败，服务可能还在启动中"
echo ""
echo "日志文件:"
echo "  FastAPI: ${BACKEND_DIR}/fastapi.log"
echo "  Celery: ${BACKEND_DIR}/celery.log"
echo ""
echo "按任意键退出..."
read -n 1 -s