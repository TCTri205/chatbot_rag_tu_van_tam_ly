@echo off
echo Creating admin account with admin@gmail.com...
type scripts\create_admin_gmail.py | docker compose exec -T backend python -
echo.
echo Done. You can now login with:
echo   Email: admin@gmail.com
echo   Password: abcd1234
pause
