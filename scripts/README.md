# Phase 2 Scripts and Tools

Collection of scripts to help deploy, verify, and test Phase 2 implementation.

## 📁 Available Scripts

### 🚀 quick_start_phase2.bat

**One-click setup script** - Automates the entire deployment process.

**What it does**:

- Builds Docker containers
- Starts all services (nginx, backend, db, redis, chroma)
- Runs database migrations
- Verifies system health
- Opens API documentation in browser

**Usage**:

```bash
quick_start_phase2.bat
```

**When to use**: First time setup or after major changes.

---

### ✅ verify_phase2.bat

**System verification** - Checks that all services are running correctly.

**What it does**:

- Checks Docker containers status
- Runs database migrations (if needed)
- Verifies system_settings table
- Checks ChromaDB health
- Opens API docs

**Usage**:

```bash
verify_phase2.bat
```

**When to use**: After deployment to confirm everything is working.

---

### 🧪 test_phase2_apis.bat

**API testing** - Interactive script to test all Phase 2 endpoints.

**What it does**:

- Tests session initialization
- Tests crisis detection
- Tests normal chat
- Tests chat history
- Tests session info

**Usage**:

```bash
test_phase2_apis.bat
```

**When to use**: To verify API functionality manually.

---

### 📋 PHASE2_VERIFICATION_CHECKLIST.md

**Manual checklist** - Comprehensive step-by-step verification guide.

**Includes**:

- Pre-deployment checks
- Deployment steps
- API testing procedures
- Database verification
- PDF ingestion test (optional)
- Issue tracking
- Sign-off section

**When to use**: For thorough testing or documentation purposes.

---

## 🏁 Quick Start Guide

### For First-Time Setup

1. **Run quick start script**:

   ```bash
   quick_start_phase2.bat
   ```

2. **Wait for completion** (may take 2-3 minutes for docker build)

3. **Verify in browser**: API docs should open automatically at <http://localhost:8080/api/v1/docs>

4. **(Optional) Test APIs**:

   ```bash
   test_phase2_apis.bat
   ```

### For Verification Only

If services are already running:

```bash
verify_phase2.bat
```

### For Detailed Testing

Follow the manual checklist:

```bash
# Open in text editor
PHASE2_VERIFICATION_CHECKLIST.md
```

---

## 🔧 Troubleshooting

### Issue: "Docker command not found"

**Solution**: Install Docker Desktop for Windows

### Issue: "Port 8080 already in use"

**Solution**:

- Stop other services using port 8080
- Or modify docker-compose.yml nginx port mapping

### Issue: "Database system is starting up"

**Solution**:

- The scripts now automatically wait for PostgreSQL to be ready (up to 60 seconds)
- If error persists, manually check: `docker-compose exec db pg_isready -U postgres`
- Restart PostgreSQL: `docker-compose restart db`
- View logs: `docker-compose logs db`

### Issue: "Migrations failed"

**Solution**:

- Check backend logs: `docker-compose logs backend`
- Verify database is running: `docker-compose ps`
- Try manual migration: `docker-compose exec backend alembic upgrade head`

### Issue: "ChromaDB not responding"

**Solution**:

- Check ChromaDB logs: `docker-compose logs chroma`
- Restart service: `docker-compose restart chroma`
- Verify port 8001 is not blocked

### Issue: "API returns 500 error"

**Solution**:

- Check GOOGLE_API_KEY in `.env`
- View backend logs: `docker-compose logs backend --tail=100`
- Verify all services are healthy: `docker-compose ps`

---

## 📊 Success Criteria

Phase 2 is successfully deployed when:

- ✅ All 5 Docker containers are running
- ✅ API docs show 6 endpoint groups (Health, Auth, Chat, Sessions, Moods)
- ✅ Session init returns valid session_id
- ✅ Crisis detection returns hotline info
- ✅ Normal chat returns AI response
- ✅ System_settings table has 3 records
- ✅ Messages saved to database with rag_sources field

---

## 📖 Additional Documentation

- **Deployment Guide**: `PHASE2_DEPLOYMENT.md` - Detailed manual deployment instructions
- **Implementation Walkthrough**: See artifacts - Complete technical documentation
- **Architecture**: `docs/SYSTEM_ARCHITECTURE.md` - System design overview

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `docker-compose logs <service_name>`
2. Review PHASE2_VERIFICATION_CHECKLIST.md
3. Consult PHASE2_DEPLOYMENT.md troubleshooting section
4. Check implementation walkthrough for architecture details

---

## 📝 Notes

- Scripts are designed for Windows (`.bat` files)
- Requires Docker and curl to be installed
- Some tests require manual input (session_id, conversation_id)
- Mood tracking tests require user authentication (not included in basic tests)

---

**Last Updated**: December 15, 2024  
**Phase**: 2 - RAG Engine & Core Logic  
**Status**: Ready for Testing
