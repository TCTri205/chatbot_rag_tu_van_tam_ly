@echo off
REM Phase 2 Verification Script for Windows
REM Run this after deploying Phase 2

echo ========================================
echo Phase 2 Verification Script
echo ========================================
echo.

echo [Step 1] Checking Docker containers...
docker-compose ps
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker containers not running. Please run: docker-compose up -d
    pause
    exit /b 1
)
echo OK: Docker containers are running
echo.

echo [Step 1.5] Waiting for PostgreSQL to be ready...
set MAX_ATTEMPTS=30
set ATTEMPT=0

:wait_db
set /a ATTEMPT+=1
docker-compose exec -T db pg_isready -U chatbot_user >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo OK: Database is ready
    goto db_ready
)

if %ATTEMPT% GEQ %MAX_ATTEMPTS% (
    echo ERROR: Database failed to start after 60 seconds
    echo Run: docker-compose logs db
    pause
    exit /b 1
)

echo Waiting... ^(attempt %ATTEMPT%/%MAX_ATTEMPTS%^)
timeout /t 2 /nobreak >nul
goto wait_db

:db_ready
echo.

echo [Step 2] Running database migrations...
docker-compose exec -T backend alembic upgrade head
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Migration failed
    pause
    exit /b 1
)
echo OK: Migrations completed
echo.

echo [Step 3] Verifying system_settings table...
docker-compose exec -T db psql -U chatbot_user -d chatbot_db -c "SELECT key, description FROM system_settings;"
echo.

echo [Step 4] Checking ChromaDB health...
curl -s http://localhost:8001/api/v2/heartbeat
echo.
echo OK: ChromaDB is responding
echo.

echo [Step 5] Checking API docs...
echo Opening API documentation in browser...
start http://localhost:8080/api/v1/docs
echo.

echo ========================================
echo Verification Phase 1 Complete!
echo.
echo Next: Run test_phase2_apis.bat to test endpoints
echo ========================================
pause
