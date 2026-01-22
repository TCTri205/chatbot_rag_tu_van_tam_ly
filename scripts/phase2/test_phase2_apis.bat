@echo off
REM Phase 2 API Testing Script
REM Tests all Phase 2 endpoints

setlocal enabledelayedexpansion

echo ========================================
echo Phase 2 API Testing Script
echo ========================================
echo.

echo [Pre-flight] Checking system health...
echo.

REM Check Database
echo Checking PostgreSQL...
set MAX_ATTEMPTS=15
set ATTEMPT=0

:wait_db_test
set /a ATTEMPT+=1
docker-compose exec -T db pg_isready -U chatbot_user >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Database is ready
    goto db_ready_test
)

if %ATTEMPT% GEQ %MAX_ATTEMPTS% (
    echo [ERROR] Database not ready after 30 seconds
    echo Run: docker-compose up -d
    pause
    exit /b 1
)

timeout /t 2 /nobreak >nul
goto wait_db_test

:db_ready_test

REM Check Backend
echo Checking Backend API...
set MAX_ATTEMPTS_API=15
set ATTEMPT_API=0

:wait_backend
set /a ATTEMPT_API+=1
curl -s http://localhost:8080/api/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Backend is responding
    goto backend_ready
)

if %ATTEMPT_API% GEQ %MAX_ATTEMPTS_API% (
    echo [ERROR] Backend not responding after 30 seconds
    echo Run: docker-compose logs backend
    pause
    exit /b 1
)

timeout /t 2 /nobreak >nul
goto wait_backend

:backend_ready
echo.
echo All systems ready!
echo.

REM Test 1: Session Init
echo [Test 1] Initializing session...
curl -X POST http://localhost:8080/api/v1/sessions/init ^
  -H "Content-Type: application/json" ^
  -d "{}" > session_response.json

REM Parse session_id from response (requires jq or manual extraction)
echo Response saved to session_response.json
echo Please extract session_id from the response and set it below:
echo.
type session_response.json
echo.

set /p SESSION_ID="Enter SESSION_ID from above: "
echo Using SESSION_ID: %SESSION_ID%
echo.

REM Test 2: Crisis Detection
echo [Test 2] Testing crisis detection...
echo.
curl -X POST http://localhost:8080/api/v1/chat ^
  -H "Content-Type: application/json" ^
  -H "X-Session-ID: %SESSION_ID%" ^
  -d "{\"content\": \"tôi muốn chết\"}"
echo.
echo.
echo Expected: Crisis response with hotlines (is_crisis: true)
echo.
pause

REM Test 3: Normal Chat
echo [Test 3] Testing normal chat...
echo.
curl -X POST http://localhost:8080/api/v1/chat ^
  -H "Content-Type: application/json" ^
  -H "X-Session-ID: %SESSION_ID%" ^
  -d "{\"content\": \"xin chào\"}"
echo.
echo.
echo Expected: Normal response (is_crisis: false, may have empty sources)
echo.
pause

REM Test 4: Chat History
echo [Test 4] Getting chat history...
REM Extract conversation_id from session_response.json first
set /p CONV_ID="Enter CONVERSATION_ID from session_response.json: "

curl -X GET "http://localhost:8080/api/v1/chat/history?conversation_id=%CONV_ID%&limit=10"
echo.
pause

REM Test 5: Session Info
echo [Test 5] Getting session info...
curl -X GET http://localhost:8080/api/v1/sessions/info ^
  -H "X-Session-ID: %SESSION_ID%"
echo.
pause

echo ========================================
echo API Testing Complete!
echo.
echo For mood tracking tests, you need to login first.
echo See PHASE2_DEPLOYMENT.md for authentication steps.
echo ========================================

del session_response.json
pause
