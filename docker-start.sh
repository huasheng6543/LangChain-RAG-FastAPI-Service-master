#!/bin/bash
set -e

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
FASTAPI_PORT=8000

ACTION="${1:-}"

show_help() {
    echo "================================================"
    echo "    RAG Docker Service Manager"
    echo "================================================"
    echo ""
    echo "Usage: docker-start.sh [action]"
    echo ""
    echo "Actions:"
    echo "   start      - Start all services (FastAPI, MySQL, Redis, Milvus, Celery)"
    echo "   stop       - Stop all services"
    echo "   restart    - Restart all services"
    echo "   status     - Show service status"
    echo "   logs       - View container logs"
    echo "   build      - Build Docker images"
    echo "   clean      - Clean all containers and volumes"
    echo ""
    echo "Service URLs (when running):"
    echo "   FastAPI: http://localhost:$FASTAPI_PORT"
    echo "   API Docs: http://localhost:$FASTAPI_PORT/docs"
    echo "   Milvus: http://localhost:19530"
    echo ""
}

action_build() {
    echo ""
    echo "================================================"
    echo "    Building Docker Images"
    echo "================================================"
    echo ""
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    echo ""
    echo "OK: Build completed successfully!"
}

action_start() {
    echo ""
    echo "================================================"
    echo "    Starting RAG Services with Docker"
    echo "================================================"
    echo ""

    echo "[1/4] Checking Docker availability..."
    if ! command -v docker &> /dev/null; then
        echo "   ERROR: Docker is not installed"
        exit 1
    fi
    if ! docker info &> /dev/null; then
        echo "   ERROR: Docker is not running"
        exit 1
    fi
    echo "   OK: Docker is available"

    echo ""
    echo "[2/4] Creating log directories..."
    mkdir -p "$PROJECT_DIR/backend/logs"
    mkdir -p "$PROJECT_DIR/backend/data"
    echo "   OK: Logs and data directories created"

    echo ""
    echo "[3/4] Starting services..."
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" up -d

    echo ""
    echo "[4/4] Waiting for services to be ready..."
    echo ""

    echo "   Waiting for MySQL..."
    until docker-compose -f "$COMPOSE_FILE" exec -T mysql mysqladmin ping -h localhost &> /dev/null; do
        sleep 5
    done
    echo "   OK: MySQL is ready"

    echo "   Waiting for Redis..."
    until docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping &> /dev/null; do
        sleep 3
    done
    echo "   OK: Redis is ready"

    echo "   Waiting for FastAPI..."
    until curl -s "http://localhost:$FASTAPI_PORT/health/live" &> /dev/null; do
        sleep 5
    done
    echo "   OK: FastAPI is ready"

    echo ""
    echo "================================================"
    echo "    All services started successfully!"
    echo "================================================"
    echo ""
    echo "Running Services:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    echo "Service URLs:"
    echo "   FastAPI: http://localhost:$FASTAPI_PORT"
    echo "   API Docs: http://localhost:$FASTAPI_PORT/docs"
    echo "   Milvus: http://localhost:19530"
    echo ""
    echo "Logs:"
    echo "   FastAPI: ./docker-start.sh logs fastapi"
    echo "   Celery:  ./docker-start.sh logs celery"
    echo ""
}

action_stop() {
    echo ""
    echo "================================================"
    echo "    Stopping RAG Services"
    echo "================================================"
    echo ""
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" stop
    echo ""
    echo "Services stopped."
}

action_restart() {
    action_stop
    action_start
}

action_status() {
    echo ""
    echo "================================================"
    echo "    RAG Services Status"
    echo "================================================"
    echo ""
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    echo "Health Check:"
    curl -s "http://localhost:$FASTAPI_PORT/health/live" || echo "Service not running"
    echo ""
}

action_logs() {
    SERVICE="${2:-}"
    if [ -z "$SERVICE" ]; then
        echo ""
        echo "================================================"
        echo "    Viewing All Container Logs"
        echo "================================================"
        echo ""
        cd "$PROJECT_DIR"
        docker-compose -f "$COMPOSE_FILE" logs -f
    else
        echo ""
        echo "================================================"
        echo "    Viewing $SERVICE Logs"
        echo "================================================"
        echo ""
        cd "$PROJECT_DIR"
        docker-compose -f "$COMPOSE_FILE" logs -f "$SERVICE"
    fi
}

action_clean() {
    echo ""
    echo "================================================"
    echo "    Cleaning RAG Services"
    echo "================================================"
    echo ""
    echo "WARNING: This will remove all containers, images, and volumes!"
    echo "All data will be lost!"
    echo ""
    read -p "Are you sure you want to clean? (Y/N): " CONFIRM
    if [ "$CONFIRM" != "Y" ] && [ "$CONFIRM" != "y" ]; then
        echo ""
        echo "Operation cancelled."
        exit 0
    fi

    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" down -v --rmi all
    echo ""
    echo "Clean completed."
}

case "$ACTION" in
    start)
        action_start
        ;;
    stop)
        action_stop
        ;;
    restart)
        action_restart
        ;;
    status)
        action_status
        ;;
    logs)
        action_logs
        ;;
    build)
        action_build
        ;;
    clean)
        action_clean
        ;;
    *)
        show_help
        ;;
esac
