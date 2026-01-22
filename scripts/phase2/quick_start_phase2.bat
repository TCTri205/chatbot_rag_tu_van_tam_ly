@echo off
REM Quick Start Script for Phase 2
REM Automates common setup steps

echo ========================================
echo Phase 2 Quick Start
echo ========================================
echo.

echo This script will:
echo 1. Build Docker containers
echo 2. Start all services
echo 3. Run database migrations
echo 4. Verify system health
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

echo.
echo [1/4] Building Docker containers...
echo This may take a few minutes on first run...
docker-compose build
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker build failed
    echo Please check Docker is running and try again
    pause
    exit /b 1
)
echo OK: Build successful
echo.

echo [2/4] Starting services...
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to start services
    pause
    exit /b 1
)
echo OK: Services started
echo.

echo [2.5/4] Waiting for PostgreSQL to be ready...
set MAX_ATTEMPTS=30
set ATTEMPT=0

:wait_db_quick
set /a ATTEMPT+=1
docker-compose exec -T db pg_isready -U chatbot_user >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo OK: Database is ready
    goto db_ready_quick
)

if %ATTEMPT% GEQ %MAX_ATTEMPTS% (
    echo ERROR: Database failed to start after 60 seconds
    echo Run: docker-compose logs db
    pause
    exit /b 1
)

echo Waiting... ^(attempt %ATTEMPT%/%MAX_ATTEMPTS%^)
timeout /t 2 /nobreak >nul
goto wait_db_quick

:db_ready_quick
echo.

echo [3/4] Running database migrations...
docker-compose exec -T backend alembic upgrade head
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Migration may have failed
    echo This is normal if migrations were already run
)
echo.

echo [4/4] Verifying system health...
echo.

echo Checking Backend...
curl -s http://localhost:8080/api/health > nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Backend is responding
) else (
    echo [WARN] Backend not responding yet - may need more time
)

echo Checking ChromaDB...
curl -s http://localhost:8001/api/v2/heartbeat > nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] ChromaDB is responding
) else (
    echo [WARN] ChromaDB not responding - check docker-compose logs chroma
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Open API docs: http://localhost:8080/api/v1/docs
echo 2. Run verify_phase2.bat for detailed checks
echo 3. Run test_phase2_apis.bat to test endpoints
echo 4. Add PDF files to data/ and run ingestion (optional)
echo.
echo Useful commands:
echo   docker-compose logs backend    - View backend logs
echo   docker-compose logs chroma     - View ChromaDB logs
echo   docker-compose ps              - Check container status
echo   docker-compose down            - Stop all services
echo.

start http://localhost:8080/api/v1/docs

pause
