@echo off
echo ========================================
echo   DATABASE USER CHECK
echo ========================================
echo.

type scripts\check_users.py | docker compose exec -T backend python -

echo.
echo ========================================
echo   TEST LOGIN API
echo ========================================
echo.

echo Testing login with admin@example.com...
curl -X POST "http://localhost:8080/api/v1/auth/login/" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@example.com\",\"password\":\"abcd1234\"}"

echo.
echo.
echo Testing login with admin@gmail.com...
curl -X POST "http://localhost:8080/api/v1/auth/login/" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@gmail.com\",\"password\":\"abcd1234\"}"

echo.
pause
