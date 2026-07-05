@echo off
chcp 65001 >nul
title RAG 后端服务一键停止脚本

echo ================================================
echo    RAG 后端微服务工程化底座 - 一键停止脚本
echo ================================================
echo.

echo [1/6] 停止 FastAPI...
taskkill /F /IM python.exe 2>nul
echo   OK: FastAPI 已停止


echo.
echo [2/6] 停止 Celery...
taskkill /F /IM celery.exe 2>nul
echo   OK: Celery 已停止


echo.
echo [3/6] 停止 Redis...
taskkill /F /IM redis-server.exe 2>nul
echo   OK: Redis 已停止


echo.
echo [4/6] 停止 Milvus...
docker stop rag-milvus 2>nul
echo   OK: Milvus 已停止


echo.
echo [5/6] 释放端口...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :6379') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :19530') do taskkill /F /PID %%a 2>nul
echo   OK: 端口已释放


echo.
echo [6/6] 清理临时文件...
del /f /q "%~dp0backend\*.pid" 2>nul
echo   OK: 临时文件已清理


echo.
echo ================================================
echo    服务停止完成!
echo ================================================
echo.
echo 所有服务已停止，端口已释放。
echo.
echo 按任意键退出...
pause >nul