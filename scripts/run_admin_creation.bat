@echo off
echo Copying script content to container...
type scripts\create_default_admin.py | docker compose exec -T backend sh -c "cat > /app/create_default_admin.py"
if %errorlevel% neq 0 (
    echo Failed to copy script content.
    exit /b %errorlevel%
)

echo Executing script in container...
docker compose exec backend python /app/create_default_admin.py
if %errorlevel% neq 0 (
    echo Failed to execute script.
    exit /b %errorlevel%
)

echo Done.
