#!/bin/bash
# Database Backup Script for Chatbot RAG TamLy
# Automatically backs up PostgreSQL database with compression and rotation

set -e  # Exit on error

# Configuration
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_DIR="./backups"
RETENTION_DAYS=30

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Chatbot RAG Database Backup ===${NC}"
echo "Started at: $(date)"

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Database credentials from .env
source .env 2>/dev/null || true
DB_USER=${POSTGRES_USER:-chatbot_user}
DB_NAME=${POSTGRES_DB:-chatbot_db}

# Perform backup
echo -e "${YELLOW}Creating backup...${NC}"
docker-compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_DIR/db_$TIMESTAMP.sql"

# Check if backup was successful
if [ -f "$BACKUP_DIR/db_$TIMESTAMP.sql" ]; then
    # Compress backup
    echo -e "${YELLOW}Compressing backup...${NC}"
    gzip "$BACKUP_DIR/db_$TIMESTAMP.sql"
    
    BACKUP_FILE="$BACKUP_DIR/db_$TIMESTAMP.sql.gz"
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    
    echo -e "${GREEN}✓ Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE)${NC}"
    
    # Delete old backups
    echo -e "${YELLOW}Cleaning up old backups (older than $RETENTION_DAYS days)...${NC}"
    find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    
    # List remaining backups
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "db_*.sql.gz" | wc -l)
    echo -e "${GREEN}✓ Cleanup complete. Total backups: $BACKUP_COUNT${NC}"
else
    echo -e "${RED}✗ Backup failed!${NC}"
    exit 1
fi

echo "Finished at: $(date)"
