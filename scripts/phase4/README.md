# Phase 4 Scripts

Automated scripts for production deployment, verification, and maintenance.

## Quick Start

### Windows

```bash
scripts\phase4\quick_start_phase4.bat
```

### Linux/Mac

```bash
chmod +x scripts/phase4/quick_start_phase4.sh
./scripts/phase4/quick_start_phase4.sh
```

## Scripts Overview

### Deployment

- `quick_start_phase4.bat` - One-command production deployment
  - Builds Docker images
  - Starts all services (including monitoring)
  - Runs database migrations
  - Performs health checks

### Verification

- `verify_phase4.bat` - Comprehensive testing suite
  - Security headers validation
  - Monitoring endpoints check
  - Rate limiting test
  - Configuration audit

### Backup

- `backup.bat` (Windows) - Database backup with rotation
- `backup.sh` (Linux) - Database backup with rotation
  - Creates timestamped backups
  - Compresses using gzip/7-Zip
  - Automatic cleanup (30-day retention)

## Usage

### Initial Deployment

1. Ensure `.env` is configured with production values
2. Run `quick_start_phase4.bat`
3. Verify with `verify_phase4.bat`
4. Access services at displayed URLs

### Daily Backup

Set up Windows Task Scheduler:

```
Action: Start a program
Program: D:\Projects_IT\chatbot_rag_tu_van_tam_ly\scripts\backup.bat
Schedule: Daily at 2:00 AM
```

### Monitoring Access

- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3000> (admin/admin)
- Metrics: <http://localhost:8080/api/v1/metrics>
