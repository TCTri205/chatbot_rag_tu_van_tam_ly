@echo off
REM Quick Start Script for Phase 4 Production Deployment
REM This script builds and starts all services including monitoring stack

setlocal enabledelayedexpansion

echo =============================================
echo   Phase 4: Production Deployment
echo   Chatbot RAG Tu Van Tam Ly
echo =============================================
echo.

REM Check if docker-compose is available
where docker-compose >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] docker-compose not found! Please install Docker Desktop.
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Creating from .env.example...
    copy .env.example .env
    echo.
    echo [IMPORTANT] Please edit .env file and set:
    echo   - SECRET_KEY (generate with: openssl rand -hex 32)
    echo   - GOOGLE_API_KEY
    echo   - Production passwords
    echo.
    pause
)

echo Step 1: Stopping existing containers...
docker-compose down

echo.
echo Step 2: Building production images (no cache)...
docker-compose build --no-cache

if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    exit /b 1
)

echo.
echo Step 3: Starting all services...
docker-compose up -d

if %errorlevel% neq 0 (
    echo [ERROR] Service start failed!
    exit /b 1
)

echo.
echo Step 4: Waiting for database to be ready...
set DB_READY=0
set RETRY_COUNT=0
set MAX_RETRIES=30

:wait_db_loop
set /a RETRY_COUNT+=1
if %RETRY_COUNT% gtr %MAX_RETRIES% (
    echo [ERROR] Database failed to start after %MAX_RETRIES% attempts
    goto skip_migration
)

REM Check if database is ready using pg_isready
docker-compose exec -T db pg_isready -U chatbot_user >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Database is ready after %RETRY_COUNT% attempts
    set DB_READY=1
    goto db_ready
)

echo Waiting for database... (attempt %RETRY_COUNT%/%MAX_RETRIES%)
timeout /t 2 /nobreak >nul
goto wait_db_loop

:db_ready
echo.
echo Step 5: Running database migrations...
set MIGRATION_SUCCESS=0
set MIGRATION_RETRY=0
set MAX_MIGRATION_RETRIES=3

:migration_loop
set /a MIGRATION_RETRY+=1
if %MIGRATION_RETRY% gtr %MAX_MIGRATION_RETRIES% (
    echo [ERROR] Migration failed after %MAX_MIGRATION_RETRIES% attempts
    goto skip_migration
)

echo Attempting migration (try %MIGRATION_RETRY%/%MAX_MIGRATION_RETRIES%)...
docker-compose exec -T backend alembic upgrade head

if %errorlevel% equ 0 (
    echo [OK] Migrations completed successfully
   set MIGRATION_SUCCESS=1
    goto after_migration
)

echo [WARN] Migration attempt %MIGRATION_RETRY% failed, retrying in 5 seconds...
timeout /t 5 /nobreak >nul
goto migration_loop

:skip_migration
echo [WARN] Skipping migrations due to errors
echo [INFO] You can run migrations manually: docker-compose exec backend alembic upgrade head

:after_migration

echo.
echo Step 6: Health checks...
echo.

REM Health check - Nginx
echo [CHECK] Nginx Gateway...
curl -f http://localhost:8080/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Nginx is running
) else (
    echo   [WARN] Nginx health check failed
)

REM Health check - Backend
echo [CHECK] Backend API...
curl -f http://localhost:8080/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Backend is healthy
) else (
    echo   [WARN] Backend not responding
)

REM Health check - Prometheus
echo [CHECK] Prometheus...
curl -f http://localhost:9090/-/healthy >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Prometheus is running
) else (
    echo   [WARN] Prometheus not responding
)

REM Health check - Grafana (allow extra time for startup)
echo [CHECK] Grafana...
timeout /t 5 /nobreak >nul
curl -f http://localhost:3000/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Grafana is running
) else (
    echo   [WARN] Grafana not responding (may still be starting)
)

echo.
echo =============================================
echo   Deployment Complete!
echo =============================================
echo.
echo Services:
echo   - Frontend:    http://localhost:8080
echo   - API Docs:    http://localhost:8080/api/v1/docs
echo   - Prometheus:  http://localhost:9090
echo   - Grafana:     http://localhost:3000 (admin/admin)
echo   - Metrics:     http://localhost:8080/api/v1/metrics
echo.
echo Monitoring:
echo   1. Open Grafana: http://localhost:3000
echo   2. Login with admin/admin
echo   3. Navigate to Dashboards
echo.
echo Next Steps:
echo   1. Test the chat interface
echo   2. Check Prometheus targets
echo   3. Review Grafana dashboard
echo   4. Run verification: scripts\phase4\verify_phase4.bat
echo.
pause
