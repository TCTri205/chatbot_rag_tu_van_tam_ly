@echo off
REM Build Tailwind CSS for production (Windows version)
REM This script compiles Tailwind CSS with minification for production use

echo 🎨 Building Tailwind CSS for production...

REM Check if npx is available
where npx >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error: npx is not installed. Please install Node.js and npm.
    exit /b 1
)

REM Build Tailwind CSS
npx tailwindcss -i ./static/css/tailwind.source.css -o ./static/css/tailwind.css --minify

if %ERRORLEVEL% EQU 0 (
    echo ✅ Tailwind CSS built successfully!
    echo 📊 Output file: ./static/css/tailwind.css
    
    REM Show file size
    if exist "./static/css/tailwind.css" (
        for %%A in ("./static/css/tailwind.css") do (
            set SIZE=%%~zA
        )
        set /a SIZE_KB=!SIZE! / 1024
        echo 📦 File size: !SIZE_KB! KB
    )
) else (
    echo ❌ Build failed!
    exit /b 1
)
