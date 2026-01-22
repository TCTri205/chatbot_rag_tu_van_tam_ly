@echo off
REM Database Backup Script for Chatbot RAG TamLy (Windows)
REM Automatically backs up PostgreSQL database with compression and rotation

setlocal enabledelayedexpansion

echo ========================================
echo   Chatbot RAG Database Backup
echo ========================================
echo Started at: %date% %time%
echo.

REM Configuration
set BACKUP_DIR=.\backups
set RETENTION_DAYS=30

REM Create timestamp (YYYY-MM-DD_HH-MM-SS)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%-%datetime:~12,2%

REM Create backup directory if not exists
if not exist "%BACKUP_DIR%" (
    echo Creating backup directory...
    mkdir "%BACKUP_DIR%"
)

REM Load database credentials from .env
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    if "%%a"=="POSTGRES_USER" set DB_USER=%%b
    if "%%a"=="POSTGRES_DB" set DB_NAME=%%b
)

REM Default values if not found
if not defined DB_USER set DB_USER=chatbot_user
if not defined DB_NAME set DB_NAME=chatbot_db

REM Perform backup
echo Creating backup...
docker-compose exec -T db pg_dump -U %DB_USER% %DB_NAME% > "%BACKUP_DIR%\db_%TIMESTAMP%.sql"

if exist "%BACKUP_DIR%\db_%TIMESTAMP%.sql" (
    echo Compressing backup...
    
    REM Check if 7-Zip is available
    where 7z >nul 2>&1
    if %errorlevel% equ 0 (
        7z a -tgzip "%BACKUP_DIR%\db_%TIMESTAMP%.sql.gz" "%BACKUP_DIR%\db_%TIMESTAMP%.sql" >nul
        del "%BACKUP_DIR%\db_%TIMESTAMP%.sql"
        echo [SUCCESS] Backup created: %BACKUP_DIR%\db_%TIMESTAMP%.sql.gz
    ) else (
        echo [WARNING] 7-Zip not found. Backup saved as .sql (uncompressed)
        echo [INFO] Install 7-Zip for compression: https://www.7-zip.org/
    )
    
    REM Delete old backups
    echo Cleaning up old backups (older than %RETENTION_DAYS% days)...
    forfiles /P "%BACKUP_DIR%" /M db_*.sql* /D -%RETENTION_DAYS% /C "cmd /c del @path" 2>nul
    
    REM Count remaining backups
    set COUNT=0
    for %%f in (%BACKUP_DIR%\db_*.sql*) do set /a COUNT+=1
    echo [SUCCESS] Cleanup complete. Total backups: !COUNT!
) else (
    echo [ERROR] Backup failed!
    exit /b 1
)

echo.
echo Finished at: %date% %time%
echo ========================================
