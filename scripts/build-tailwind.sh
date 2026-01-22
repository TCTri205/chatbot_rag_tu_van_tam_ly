#!/bin/bash
# Build Tailwind CSS for production
# This script compiles Tailwind CSS with minification for production use

echo "🎨 Building Tailwind CSS for production..."

# Check if npx is available
if ! command -v npx &> /dev/null; then
    echo "❌ Error: npx is not installed. Please install Node.js and npm."
    exit 1
fi

# Build Tailwind CSS
npx tailwindcss -i ./static/css/tailwind.source.css -o ./static/css/tailwind.css --minify

if [ $? -eq 0 ]; then
    echo "✅ Tailwind CSS built successfully!"
    echo "📊 Output file: ./static/css/tailwind.css"
    
    # Show file size
    if [ -f "./static/css/tailwind.css" ]; then
        SIZE=$(wc -c < "./static/css/tailwind.css")
        SIZE_KB=$((SIZE / 1024))
        echo "📦 File size: ${SIZE_KB} KB"
    fi
else
    echo "❌ Build failed!"
    exit 1
fi
