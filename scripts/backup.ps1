# Automated Database Backup Script for Windows
# Backs up PostgreSQL database with rotation policy

$TIMESTAMP = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$BACKUP_DIR = ".\backups"
$DB_USER = "chatbot_user"
$DB_NAME = "chatbot_db"
$RETENTION_DAYS = 30

# Create backup directory if not exists
if (!(Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR
}

Write-Host "Starting database backup at $TIMESTAMP"

# Dump database using Docker exec
docker-compose exec -T db pg_dump -U $DB_USER -d $DB_NAME > "$BACKUP_DIR\db_$TIMESTAMP.sql"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database dump successful"
    
    # Compress backup
    Compress-Archive -Path "$BACKUP_DIR\db_$TIMESTAMP.sql" -DestinationPath "$BACKUP_DIR\db_$TIMESTAMP.zip"
    Remove-Item "$BACKUP_DIR\db_$TIMESTAMP.sql"
    
    Write-Host "✓ Backup compressed: db_$TIMESTAMP.zip"
    
    # Delete old backups (older than RETENTION_DAYS)
    $cutoffDate = (Get-Date).AddDays(-$RETENTION_DAYS)
    Get-ChildItem $BACKUP_DIR -Filter "db_*.zip" | Where-Object {
        $_.LastWriteTime -lt $cutoffDate
    } | Remove-Item
    
    Write-Host "✓ Old backups cleaned (retention: $RETENTION_DAYS days)"
    Write-Host "Backup completed successfully!"
} else {
    Write-Host "✗ Database backup failed!"
    exit 1
}
