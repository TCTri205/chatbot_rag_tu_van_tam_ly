@echo off
REM Script to create admin user in Docker container
REM Usage: create_admin_docker.bat <username> <email> <password> [role]
REM Example: create_admin_docker.bat admin admin@example.com MyPassword123 admin

if "%~3"=="" (
    echo Usage: create_admin_docker.bat username email password [role]
    echo Example: create_admin_docker.bat admin admin@example.com Pass123! admin
    echo.
    echo Role can be: admin or super_admin (default: admin^)
    exit /b 1
)

set USERNAME=%~1
set EMAIL=%~2
set PASSWORD=%~3
set ROLE=%~4

if "%ROLE%"=="" set ROLE=admin

echo ==========================================
echo    Tao Tai Khoan Admin - TamLy Bot
echo ==========================================
echo.
echo Username: %USERNAME%
echo Email: %EMAIL%
echo Role: %ROLE%
echo.

REM Find backend container name
echo Searching for backend container...
for /f "tokens=*" %%i in ('docker ps --filter "name=backend" --format "{{.Names}}"') do set CONTAINER_NAME=%%i

if "%CONTAINER_NAME%"=="" (
    echo ERROR: Backend container not found!
    echo Please make sure Docker containers are running.
    echo Run: docker-compose up -d
    exit /b 1
)

echo Found container: %CONTAINER_NAME%
echo Creating admin user...
echo.

docker exec %CONTAINER_NAME% python scripts/create_admin_in_docker.py %USERNAME% %EMAIL% %PASSWORD% %ROLE%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Thanh cong! Ban co the dang nhap voi:
    echo Email: %EMAIL%
    echo Password: %PASSWORD%
    echo ========================================
) else (
    echo.
    echo Loi khi tao tai khoan!
)
