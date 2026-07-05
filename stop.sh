#!/bin/bash

echo "================================================"
echo "    RAG 后端微服务工程化底座 - 一键停止脚本"
echo "================================================"
echo ""

echo "[1/6] 停止 FastAPI..."
pkill -f "uvicorn main:app" 2>/dev/null || true
echo "  OK: FastAPI 已停止"

echo ""
echo "[2/6] 停止 Celery..."
pkill -f "celery" 2>/dev/null || true
echo "  OK: Celery 已停止"

echo ""
echo "[3/6] 停止 Redis..."
redis-cli shutdown 2>/dev/null || true
pkill -f "redis-server" 2>/dev/null || true
echo "  OK: Redis 已停止"

echo ""
echo "[4/6] 停止 Milvus..."
docker stop rag-milvus 2>/dev/null || true
echo "  OK: Milvus 已停止"

echo ""
echo "[5/6] 释放端口..."
kill -9 $(lsof -ti:8000) 2>/dev/null || true
kill -9 $(lsof -ti:6379) 2>/dev/null || true
kill -9 $(lsof -ti:19530) 2>/dev/null || true
echo "  OK: 端口已释放"

echo ""
echo "[6/6] 清理临时文件..."
rm -f "${BASH_SOURCE%/*}/backend/fastapi.log" 2>/dev/null || true
rm -f "${BASH_SOURCE%/*}/backend/celery.log" 2>/dev/null || true
rm -f "${BASH_SOURCE%/*}/backend/*.pid" 2>/dev/null || true
echo "  OK: 临时文件已清理"

echo ""
echo "================================================"
echo "    服务停止完成!"
echo "================================================"
echo ""
echo "所有服务已停止，端口已释放。"
echo ""