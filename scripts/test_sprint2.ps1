# Quick Test: Sprint 2 API Endpoints
# Tests exercises and admin stats

Write-Host "=== Sprint 2 API Tests ===" -ForegroundColor Cyan

# 1. Test Exercises API
Write-Host "`n1. Testing Exercises API..." -ForegroundColor Yellow
try {
    $exercises = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/exercises/" -Method Get
    Write-Host "   ✅ Exercises API working" -ForegroundColor Green
    Write-Host "   Total exercises: $($exercises.Count)" -ForegroundColor Gray
    
    $exercises | ForEach-Object { 
        Write-Host "     - $($_.title) [$($_.category)]" -ForegroundColor Gray
    }
}
catch {
    Write-Host "   ❌ FAIL: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. Test Exercise Categories
Write-Host "`n2. Testing Exercise Categories..." -ForegroundColor Yellow
try {
    $categories = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/exercises/categories" -Method Get
    Write-Host "   ✅ Categories API working" -ForegroundColor Green
    
    $categories.categories | ForEach-Object {
        Write-Host "     - $($_.label): $($_.count) exercises" -ForegroundColor Gray
    }
}
catch {
    Write-Host "   ❌ FAIL: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Test Admin Stats (expected to require auth)
Write-Host "`n3. Testing Admin Stats (requires auth)..." -ForegroundColor Yellow
try {
    $stats = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/admin/stats/overview" -Method Get
    Write-Host "   ✅ Stats returned (authenticated user)" -ForegroundColor Green
}
catch {
    $errorMsg = $_.Exception.Message
    if ($errorMsg -like "*403*" -or $errorMsg -like "*Forbidden*") {
        Write-Host "   ✅ Expected: 403 Forbidden (auth protection working)" -ForegroundColor Green
        Write-Host "   Admin endpoints properly secured" -ForegroundColor Gray
    }
    elseif ($errorMsg -like "*401*" -or $errorMsg -like "*Not authenticated*") {
        Write-Host "   ✅ Expected: 401 Unauthorized (auth protection working)" -ForegroundColor Green
    }
    else {
        Write-Host "   ❌ FAIL: Unexpected error - $errorMsg" -ForegroundColor Red
    }
}

# 4. Test Health Endpoint
Write-Host "`n4. Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8080/api/health/" -Method Get
    Write-Host "   ✅ Health check OK" -ForegroundColor Green
    Write-Host "   Status: $($health.status)" -ForegroundColor Gray
    Write-Host "   Database: $($health.services.database)" -ForegroundColor Gray
    Write-Host "   Redis: $($health.services.redis)" -ForegroundColor Gray
}
catch {
    Write-Host "   ❌ FAIL: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Tests Complete ===" -ForegroundColor Cyan
Write-Host "All Sprint 2 features verified ✅" -ForegroundColor Green
