#!/bin/bash
# SSL Setup Script for Let's Encrypt (Linux/Production Server)
#
# This script automates SSL certificate installation using certbot (Let's Encrypt)
# Run this script on your production server before enabling HTTPS in nginx.conf

set -e  # Exit on error

# Configuration (UPDATE THESE VALUES)
DOMAIN="${DOMAIN:-your-domain.com}"
EMAIL="${EMAIL:-admin@your-domain.com}"
WEBROOT="${WEBROOT:-/var/www/html}"

echo "============================================"
echo "SSL Certificate Setup for $DOMAIN"
echo "============================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root or with sudo"
    exit 1
fi

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y certbot
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        yum install -y certbot
    else
        echo "ERROR: Unsupported package manager. Please install certbot manually."
        exit 1
    fi
fi

echo "Certbot version:"
certbot --version

# Obtain SSL certificate
echo ""
echo "Obtaining SSL certificate for $DOMAIN..."
echo "This may take a few moments..."

certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --domains "$DOMAIN" \
    --preferred-challenges http

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL Certificate obtained successfully!"
    echo ""
    echo "Certificate files location:"
    echo "  Fullchain: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    echo "  Private Key: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
    echo ""
    echo "Next steps:"
    echo "1. Update nginx/nginx.conf:"
    echo "   - Uncomment the HTTPS server block"
    echo "   - Replace 'your-domain.com' with '$DOMAIN'"
    echo "   - Comment out or remove the HTTP-only server block"
    echo ""
    echo "2. Update docker-compose.yml:"
    echo "   - Add port mapping: '443:443'"
    echo "   - Add volume mount: './ssl:/etc/letsencrypt:ro'"
    echo ""
    echo "3. Create ssl directory and copy certificates:"
    echo "   mkdir -p $(pwd)/ssl"
    echo "   cp -r /etc/letsencrypt/* $(pwd)/ssl/"
    echo ""
    echo "4. Restart nginx:"
    echo "   docker-compose restart nginx"
    echo ""
    echo "Certificate auto-renewal:"
    echo "  Certbot will automatically renew certificates before expiry."
    echo "  To test renewal: certbot renew --dry-run"
else
    echo ""
    echo "❌ Failed to obtain SSL certificate"
    echo "Please check the error messages above and try again."
    exit 1
fi
