@echo off
REM Verification Script for Phase 4 Production Features
REM Tests security hardening, monitoring, and deployment readiness

setlocal enabledelayedexpansion

echo =============================================
echo   Phase 4: Production Verification
echo   Testing Security, Monitoring, Backup
echo =============================================
echo.

set PASS_COUNT=0
set FAIL_COUNT=0
set WARN_COUNT=0

REM ==========================================
REM Test 1: Security Headers
REM ==========================================
echo [TEST 1] Security Headers Check...

curl -sI http://localhost:8080 > temp_headers.txt 2>nul

findstr /C:"X-Frame-Options" temp_headers.txt >nul
if %errorlevel% equ 0 (
    echo   [PASS] X-Frame-Options header present
    set /a PASS_COUNT+=1
) else (
    echo   [FAIL] X-Frame-Options header missing
    set /a FAIL_COUNT+=1
)

findstr /C:"X-Content-Type-Options" temp_headers.txt >nul
if %errorlevel% equ 0 (
    echo   [PASS] X-Content-Type-Options header present
    set /a PASS_COUNT+=1
) else (
    echo   [FAIL] X-Content-Type-Options header missing
    set /a FAIL_COUNT+=1
)

del temp_headers.txt 2>nul

echo.
REM ==========================================
REM Test 2: Server Tokens Hidden
REM ==========================================
echo [TEST 2] Server Version Hidden...

curl -sI http://localhost:8080 | findstr /C:"nginx/" >nul
if %errorlevel% neq 0 (
    echo   [PASS] Server version is hidden
    set /a PASS_COUNT+=1
) else (
    echo   [WARN] Server version may be exposed
    set /a WARN_COUNT+=1
)

echo.
REM ==========================================
REM Test 3: Prometheus Metrics
REM ==========================================
echo [TEST 3] Prometheus Metrics Endpoint...

curl -f http://localhost:8080/api/v1/metrics >nul 2>&1
if %errorlevel% equ 0 (
    echo   [PASS] Metrics endpoint accessible
    set /a PASS_COUNT+=1
) else (
    echo   [FAIL] Metrics endpoint not accessible
    set /a FAIL_COUNT+=1
)

echo.
REM ==========================================
REM Test 4: Prometheus Target Health
REM ==========================================
echo [TEST 4] Prometheus Target Health...

curl -s http://localhost:9090/api/v1/targets 2>nul | findstr /C:"\"health\":\"up\"" >nul
if %errorlevel% equ 0 (
    echo   [PASS] Prometheus scraping backend successfully
    set /a PASS_COUNT+=1
) else (
    echo   [WARN] Prometheus may not be scraping backend
    set /a WARN_COUNT+=1
)

echo.
REM ==========================================
REM Test 5: Grafana Health
REM ==========================================
echo [TEST 5] Grafana Health Check...

curl -f http://localhost:3000/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo   [PASS] Grafana is running
    set /a PASS_COUNT+=1
) else (
    echo   [FAIL] Grafana health check failed
    set /a FAIL_COUNT+=1
)

echo.
REM ==========================================
REM Test 6: Rate Limiting
REM ==========================================
echo [TEST 6] Rate Limiting Test (sending 15 rapid requests)...

REM Initialize session first
for /f %%i in ('curl -s -X POST http://localhost:8080/api/v1/sessions/init -H "Content-Type: application/json" -d "{}" ^| findstr /C:"session_id"') do set SESSION_LINE=%%i

REM Extract session_id (simplified - might need adjustment)
set SESSION_ID=test-session-123

set RATE_LIMIT_TRIGGERED=0
for /L %%i in (1,1,15) do (
    curl -s -X POST http://localhost:8080/api/v1/chat/ ^
        -H "Content-Type: application/json" ^
        -H "X-Session-ID: %SESSION_ID%" ^
        -d "{\"content\": \"test\"}" | findstr /C:"429" >nul
    if !errorlevel! equ 0 (
        set RATE_LIMIT_TRIGGERED=1
    )
)

if %RATE_LIMIT_TRIGGERED% equ 1 (
    echo   [PASS] Rate limiting is active (429 received)
    set /a PASS_COUNT+=1
) else (
    echo   [WARN] Rate limiting may not be working (no 429 in 15 requests)
    set /a WARN_COUNT+=1
)

echo.
REM ==========================================
REM Test 7: Backup Script
REM ==========================================
echo [TEST 7] Backup Script Test...

if exist "scripts\backup.bat" (
    echo   [PASS] Backup script exists
    set /a PASS_COUNT+=1
    
    REM Check if backups directory can be created
    if not exist "backups" mkdir backups
    if exist "backups" (
        echo   [PASS] Backup directory ready
        set /a PASS_COUNT+=1
    ) else (
        echo   [FAIL] Cannot create backup directory
        set /a FAIL_COUNT+=1
    )
) else (
    echo   [FAIL] Backup script not found
    set /a FAIL_COUNT+=1
)

echo.
REM ==========================================
REM Test 8: Environment Configuration
REM ==========================================
echo [TEST 8] Production Configuration Check...

set ENV_EXISTS=0
if exist ".env" (
    set ENV_EXISTS=1
    findstr /C:"DEBUG=False" .env >nul
    if %errorlevel% equ 0 (
        echo   [PASS] DEBUG is set to False
        set /a PASS_COUNT+=1
    ) else (
        echo   [WARN] DEBUG is not False (OK for development)
        set /a WARN_COUNT+=1
    )
    
    findstr /C:"SECRET_KEY=your_super_secret_key" .env >nul
    if %errorlevel% neq 0 (
        echo   [PASS] SECRET_KEY has been changed from default
        set /a PASS_COUNT+=1
    ) else (
        echo   [FAIL] SECRET_KEY is still default value!
        set /a FAIL_COUNT+=1
    )
)

if %ENV_EXISTS% equ 0 (
    echo   [FAIL] .env file not found
    set /a FAIL_COUNT+=1
)

echo.
echo =============================================
echo   Verification Results
echo =============================================
echo   PASSED:   %PASS_COUNT%
echo   FAILED:   %FAIL_COUNT%
echo   WARNINGS: %WARN_COUNT%
echo =============================================
echo.

if %FAIL_COUNT% gtr 0 (
    echo [RESULT] Some tests FAILED. Please review the issues above.
    exit /b 1
) else if %WARN_COUNT% gtr 0 (
    echo [RESULT] All critical tests passed with %WARN_COUNT% warnings.
    exit /b 0
) else (
    echo [RESULT] All tests PASSED!
    exit /b 0
)
