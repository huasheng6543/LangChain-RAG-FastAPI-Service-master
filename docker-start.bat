@echo off
chcp 65001 >nul
title RAG Docker Service Manager

set "PROJECT_DIR=%~dp0"
set "COMPOSE_FILE=%PROJECT_DIR%docker-compose.yml"
set "FASTAPI_PORT=8000"

set "ACTION=%1"

if "%ACTION%"=="" goto SHOW_MENU
if "%ACTION%"=="start" goto ACTION_START
if "%ACTION%"=="stop" goto ACTION_STOP
if "%ACTION%"=="restart" goto ACTION_RESTART
if "%ACTION%"=="status" goto ACTION_STATUS
if "%ACTION%"=="logs" goto ACTION_LOGS
if "%ACTION%"=="build" goto ACTION_BUILD
if "%ACTION%"=="clean" goto ACTION_CLEAN

:SHOW_MENU
echo ================================================
echo    RAG Docker Service Manager
echo ================================================
echo.
echo Usage: docker-start.bat [action]
echo.
echo Actions:
echo   start      - Start all services (FastAPI, MySQL, Redis, Milvus, Celery)
echo   stop       - Stop all services
echo   restart    - Restart all services
echo   status     - Show service status
echo   logs       - View container logs
echo   build      - Build Docker images
echo   clean      - Clean all containers and volumes
echo.
echo Service URLs (when running):
echo   FastAPI: http://localhost:%FASTAPI_PORT%
echo   API Docs: http://localhost:%FASTAPI_PORT%/docs
echo   Milvus: http://localhost:19530
echo.
set /p "ACTION=Enter action: "

if "%ACTION%"=="start" goto ACTION_START
if "%ACTION%"=="stop" goto ACTION_STOP
if "%ACTION%"=="restart" goto ACTION_RESTART
if "%ACTION%"=="status" goto ACTION_STATUS
if "%ACTION%"=="logs" goto ACTION_LOGS
if "%ACTION%"=="build" goto ACTION_BUILD
if "%ACTION%"=="clean" goto ACTION_CLEAN

echo Invalid action!
pause
exit /b 1


:ACTION_BUILD
echo.
echo ================================================
echo    Building Docker Images
echo ================================================
echo.
cd /d "%PROJECT_DIR%"
docker-compose -f "%COMPOSE_FILE%" build --no-cache
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo.
echo OK: Build completed successfully!
pause
goto END


:ACTION_START
echo.
echo ================================================
echo    Starting RAG Services with Docker
echo ================================================
echo.

echo [1/4] Checking Docker availability...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   ERROR: Docker is not installed or not running
    echo   Please install Docker Desktop and start it first
    pause
    exit /b 1
)
echo   OK: Docker is available

echo.
echo [2/4] Creating log directories...
if not exist "%PROJECT_DIR%backend\logs" (
    mkdir "%PROJECT_DIR%backend\logs"
    echo   OK: Created logs directory
) else (
    echo   OK: Logs directory exists
)
if not exist "%PROJECT_DIR%backend\data" (
    mkdir "%PROJECT_DIR%backend\data"
    echo   OK: Created data directory
) else (
    echo   OK: Data directory exists
)

echo.
echo [3/4] Starting services...
cd /d "%PROJECT_DIR%"
docker-compose -f "%COMPOSE_FILE%" up -d
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start services!
    pause
    exit /b 1
)

echo.
echo [4/4] Waiting for services to be ready...
echo.

echo   Waiting for MySQL...
:WAIT_MYSQL
docker-compose -f "%COMPOSE_FILE%" exec -T mysql mysqladmin ping -h localhost >nul 2>&1
if %errorlevel% equ 0 (
    echo   OK: MySQL is ready
) else (
    timeout /t 5 /nobreak >nul
    goto WAIT_MYSQL
)

echo   Waiting for Redis...
:WAIT_REDIS
docker-compose -f "%COMPOSE_FILE%" exec -T redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo   OK: Redis is ready
) else (
    timeout /t 3 /nobreak >nul
    goto WAIT_REDIS
)

echo   Waiting for FastAPI...
:WAIT_FASTAPI
curl -s http://localhost:%FASTAPI_PORT%/health/live >nul 2>&1
if %errorlevel% equ 0 (
    echo   OK: FastAPI is ready
) else (
    timeout /t 5 /nobreak >nul
    goto WAIT_FASTAPI
)

echo.
echo ================================================
echo    All services started successfully!
echo ================================================
echo.
echo Running Services:
docker-compose -f "%COMPOSE_FILE%" ps
echo.
echo Service URLs:
echo   FastAPI: http://localhost:%FASTAPI_PORT%
echo   API Docs: http://localhost:%FASTAPI_PORT%/docs
echo   Milvus: http://localhost:19530
echo.
echo Logs:
echo   FastAPI: docker-start.bat logs fastapi
echo   Celery:  docker-start.bat logs celery
echo.
pause
goto END


:ACTION_STOP
echo.
echo ================================================
echo    Stopping RAG Services
echo ================================================
echo.
cd /d "%PROJECT_DIR%"
docker-compose -f "%COMPOSE_FILE%" stop
echo.
echo Services stopped.
pause
goto END


:ACTION_RESTART
call :ACTION_STOP
call :ACTION_START
goto END


:ACTION_STATUS
echo.
echo ================================================
echo    RAG Services Status
echo ================================================
echo.
cd /d "%PROJECT_DIR%"
docker-compose -f "%COMPOSE_FILE%" ps
echo.
echo.
echo Health Check:
curl -s http://localhost:%FASTAPI_PORT%/health/live
echo.
pause
goto END


:ACTION_LOGS
set "SERVICE=%2"
if "%SERVICE%"=="" (
    echo.
    echo ================================================
    echo    Viewing All Container Logs
    echo ================================================
    echo.
    cd /d "%PROJECT_DIR%"
    docker-compose -f "%COMPOSE_FILE%" logs -f
) else (
    echo.
    echo ================================================
    echo    Viewing %SERVICE% Logs
    echo ================================================
    echo.
    cd /d "%PROJECT_DIR%"
    docker-compose -f "%COMPOSE_FILE%" logs -f %SERVICE%
)
goto END


:ACTION_CLEAN
echo.
echo ================================================
echo    Cleaning RAG Services
echo ================================================
echo.
echo WARNING: This will remove all containers, images, and volumes!
echo All data will be lost!
echo.
set /p "CONFIRM=Are you sure you want to clean? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo Operation cancelled.
    pause
    goto END
)

cd /d "%PROJECT_DIR%"
docker-compose -f "%COMPOSE_FILE%" down -v --rmi all
echo.
echo Clean completed.
pause
goto END


:END
exit /b 0
