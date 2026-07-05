@echo off
chcp 65001 >nul
title RAG Backend Service Starter

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "PYTHON_EXE=python"
set "REDIS_PORT=6379"
set "MYSQL_PORT=3306"
set "MILVUS_PORT=19530"
set "FASTAPI_PORT=8000"

set "MODE=%1"

if "%MODE%"=="" goto SHOW_MENU
if "%MODE%"=="1" goto MODE_VECTOR
if "%MODE%"=="2" goto MODE_LLM
if "%MODE%"=="3" goto MODE_FULL

:SHOW_MENU
echo ================================================
echo    RAG Backend Microservice - One-Click Starter
echo ================================================
echo.
echo Usage: start.bat [1^|2^|3]
echo.
echo Startup Modes:
echo   1 - Vector Mode (Doc upload/vectorization/async tasks, vLLM disabled)
echo   2 - LLM Mode (RAG retrieval + LLM inference, Milvus/Celery disabled)
echo   3 - Full Mode (All services running, short-time test)
echo.

if "%MODE%"=="1" goto MODE_VECTOR
if "%MODE%"=="2" goto MODE_LLM
if "%MODE%"=="3" goto MODE_FULL

set /p "MODE=Enter mode (1/2/3): "

if "%MODE%"=="1" goto MODE_VECTOR
if "%MODE%"=="2" goto MODE_LLM
if "%MODE%"=="3" goto MODE_FULL

echo Invalid mode selection!
pause
exit /b 1


:MODE_VECTOR
echo.
echo ================================================
echo    Mode 1: Vector Mode
echo ================================================
echo Starting: Redis + MySQL + Celery + FastAPI
echo Disabled: vLLM + Milvus
echo ================================================
echo.
goto START_COMMON


:MODE_LLM
echo.
echo ================================================
echo    Mode 2: LLM Mode
echo ================================================
echo Starting: Redis + MySQL + FastAPI (+ vLLM)
echo Disabled: Milvus + Celery
echo ================================================
echo.
set "ENABLE_VLLM=true"
goto START_COMMON


:MODE_FULL
echo.
echo ================================================
echo    Mode 3: Full Mode
echo ================================================
echo Starting: Redis + MySQL + Milvus + Celery + FastAPI (+ vLLM)
echo ================================================
echo.
set "ENABLE_VLLM=true"
set "ENABLE_MILVUS=true"
set "ENABLE_CELERY=true"
goto START_COMMON


:START_COMMON
echo [1/5] Checking Python environment...
where %PYTHON_EXE% >nul 2>&1
if %errorlevel% neq 0 (
    echo   ERROR: Python not found, please install Python 3.10+
    pause
    exit /b 1
)
echo   OK: Python environment OK


echo.
echo [2/5] Checking project directory...
if not exist "%BACKEND_DIR%" (
    echo   ERROR: Backend directory not found: %BACKEND_DIR%
    pause
    exit /b 1
)
echo   OK: Project directory OK


echo.
echo [3/5] Checking environment config...
if not exist "%BACKEND_DIR%\.env" (
    echo   ERROR: Environment config not found: %BACKEND_DIR%\.env
    pause
    exit /b 1
)
echo   OK: Environment config OK


echo.
echo [4/5] Checking dependencies...
%PYTHON_EXE% "%BACKEND_DIR%\verify_env.py"
if %errorlevel% neq 0 (
    echo   ERROR: Dependency check failed, please install missing packages
    pause
    exit /b 1
)
echo   OK: Dependencies OK


echo.
echo [5/5] Starting services...

echo.
echo --- Starting Redis ---
netstat -ano | findstr :%REDIS_PORT% >nul
if %errorlevel% equ 0 (
    echo   WARN: Port %REDIS_PORT% already in use, skipping Redis
) else (
    start "Redis" redis-server
    timeout /t 3 /nobreak >nul
    echo   OK: Redis started
)


echo.
echo --- Starting MySQL ---
netstat -ano | findstr :%MYSQL_PORT% >nul
if %errorlevel% equ 0 (
    echo   WARN: Port %MYSQL_PORT% already in use, skipping MySQL
) else (
    echo   INFO: MySQL needs manual start, please ensure MySQL is running
)


if "%ENABLE_MILVUS%"=="true" (
    echo.
    echo --- Starting Milvus ---
    netstat -ano | findstr :%MILVUS_PORT% >nul
    if %errorlevel% equ 0 (
        echo   WARN: Port %MILVUS_PORT% already in use, skipping Milvus
    ) else (
        echo   INFO: Starting Milvus...
        docker start rag-milvus 2>nul || docker run -d --name rag-milvus -p 19530:19530 -p 9091:9091 milvusdb/milvus:v2.4.5
        timeout /t 10 /nobreak >nul
        echo   OK: Milvus started
    )
)


if "%ENABLE_CELERY%"=="true" (
    echo.
    echo --- Starting Celery ---
    start "Celery" cmd /k "cd /d %BACKEND_DIR% && celery -A app.celery_config worker --loglevel=info"
    timeout /t 3 /nobreak >nul
    echo   OK: Celery started
)


echo.
echo --- Starting FastAPI ---
cd /d %BACKEND_DIR%

if "%ENABLE_VLLM%"=="true" (
    echo   INFO: Enabling vLLM local model mode
    set "ENV_VARS=VLLM_ENABLED=true"
) else (
    echo   INFO: vLLM disabled, using cloud model
    set "ENV_VARS=VLLM_ENABLED=false"
)

start "FastAPI" cmd /k "%ENV_VARS% %PYTHON_EXE% -m uvicorn main:app --host 0.0.0.0 --port %FASTAPI_PORT%"
timeout /t 5 /nobreak >nul


echo.
echo ================================================
echo    Services started successfully!
echo ================================================
echo.
echo Service URLs:
echo   FastAPI: http://localhost:%FASTAPI_PORT%
echo   API Docs: http://localhost:%FASTAPI_PORT%/docs
echo.
echo Mode Info:
if "%MODE%"=="1" (
    echo   Current Mode: Vector Mode
    echo   Available: Document upload, vectorization, async tasks
    echo   Unavailable: LLM inference, Milvus vector DB
)
if "%MODE%"=="2" (
    echo   Current Mode: LLM Mode
    echo   Available: RAG retrieval, LLM inference
    echo   Unavailable: Milvus vector DB, Celery async tasks
)
if "%MODE%"=="3" (
    echo   Current Mode: Full Mode
    echo   Available: All features
)
echo.
echo Health Check:
%PYTHON_EXE% -c "import urllib.request; print(urllib.request.urlopen('http://localhost:%FASTAPI_PORT%/health').read().decode())" 2>nul || echo   WARN: Health check failed, service may still be starting
echo.