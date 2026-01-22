# Automated Backup Setup Guide

## Overview

This guide explains how to set up automated daily backups for the PostgreSQL database using Windows Task Scheduler.

## Files

- `scripts/backup.ps1` - PowerShell backup script with compression and rotation
- `scripts/backup.sh` - Linux/Mac bash script (for reference)

## Windows Setup (Task Scheduler)

### Step 1: Test Backup Script

First, test the backup script manually:

```powershell
cd d:\Projects_IT\chatbot_rag_tu_van_tam_ly
.\scripts\backup.ps1
```

Expected output:

```
Starting database backup at 2025-12-17_02-00-00
✓ Database dump successful
✓ Backup compressed: db_2025-12-17_02-00-00.zip
✓ Old backups cleaned (retention: 30 days)
Backup completed successfully!
```

### Step 2: Create Task Scheduler Job

1. Open **Task Scheduler** (taskschd.msc)

2. Click **Create Basic Task**
   - Name: `Chatbot DB Backup`
   - Description: `Daily automated backup of psychology chatbot database`

3. **Trigger**: Daily at 2:00 AM
   - Start date: Today
   - Recur every: 1 days
   - Time: 02:00:00

4. **Action**: Start a program
   - Program/script: `powershell.exe`
   - Arguments: `-ExecutionPolicy Bypass -File "d:\Projects_IT\chatbot_rag_tu_van_tam_ly\scripts\backup.ps1"`
   - Start in: `d:\Projects_IT\chatbot_rag_tu_van_tam_ly`

5. **Settings**:
   - ✓ Allow task to be run on demand
   - ✓ Run task as soon as possible after a scheduled start is missed
   - ✓ If task fails, restart every: 5 minutes (maximum 3 attempts)

6. Click **Finish**

### Step 3: Configure Task Advanced Settings

Right-click the newly created task → **Properties**:

- **General** tab:
  - Run whether user is logged on or not: ✓
  - Run with highest privileges: ✓

- **Conditions** tab:
  - Uncheck "Start the task only if the computer is on AC power"

- **Settings** tab:
  - If the running task does not end when requested, force it to stop: ✓
  - Stop the task if it runs longer than: 1 hour

Click **OK** and enter your Windows password if prompted.

### Step 4: Test Scheduled Task

Right-click the task → **Run**

Check backup directory:

```powershell
dir .\backups\
```

You should see a new `.zip` file with timestamp.

## Backup Rotation Policy

- **Retention**: 30 days (configurable in `backup.ps1`)
- **Format**: `db_YYYY-MM-DD_HH-MM-SS.zip`
- **Location**: `./backups/` directory
- **Cleanup**: Automatic deletion of backups older than retention period

## Restore Procedure

### Windows Restore

1. Stop the backend container:

```powershell
docker-compose stop backend
```

2. Extract backup file:

```powershell
Expand-Archive -Path .\backups\db_2025-12-17_02-00-00.zip -DestinationPath .\backups\temp
```

3. Restore to database:

```powershell
Get-Content .\backups\temp\db_2025-12-17_02-00-00.sql | docker-compose exec -T db psql -U chatbot_user -d chatbot_db
```

4. Clean up and restart:

```powershell
Remove-Item -Recurse -Force .\backups\temp
docker-compose start backend
```

5. Verify restoration:

```powershell
docker-compose exec db psql -U chatbot_user -d chatbot_db -c "SELECT COUNT(*) FROM users;"
```

## Monitoring Backup Health

### Check Last Backup

```powershell
Get-ChildItem .\backups\ -Filter "db_*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

### View Task History

1. Open Task Scheduler
2. Find "Chatbot DB Backup" task
3. Click **History** tab (enable if needed)

### Email Notifications (Optional)

To get email alerts on backup failures:

1. Task Properties → **Actions** tab → **Edit**
2. Add another action: **Send an email**
   - From: <your-email@domain.com>
   - To: <admin@domain.com>
   - Subject: Backup Failed - Chatbot Database
   - SMTP server: smtp.gmail.com:587

## Troubleshooting

### Error: "Docker is not running"

Ensure Docker Desktop is running before scheduled time or add a startup action:

```powershell
# Add to beginning of backup.ps1
if (!(docker info 2>$null)) {
    Write-Host "Starting Docker Desktop..."
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Start-Sleep -Seconds 30
}
```

### Error: "Permission denied"

Run Task Scheduler as Administrator and configure task to run with highest privileges.

### Backups Too Large

Compress and move old backups to external storage:

```powershell
# Move backups older than 7 days to archive
$archiveDate = (Get-Date).AddDays(-7)
Get-ChildItem .\backups\ -Filter "db_*.zip" | Where-Object {
    $_.LastWriteTime -lt $archiveDate
} | Move-Item -Destination "E:\Archives\chatbot_backups\"
```

## Best Practices

1. **Test restores monthly** - Verify backup integrity
2. **Monitor disk space** - Ensure backup directory has sufficient space
3. **Off-site backup** - Copy backups to cloud storage (Google Drive, OneDrive)
4. **Document settings** - Keep this guide updated with any customizations

## Production Recommendations

For production deployments:

- Use managed database services (AWS RDS, Azure Database) with automated backups
- Implement Point-in-Time Recovery (PITR) for critical data
- Store backups in multiple geographic locations
- Encrypt backup files before storage
- Monitor backup success/failure via alerting system (PagerDuty, Slack)
