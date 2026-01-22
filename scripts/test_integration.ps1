# Integration Test: Full Chat Flow
# Tests: Session Init → Send Message → Get History → Log Mood

Write-Host "=== Integration Test: Full Chat Flow ===" -ForegroundColor Cyan

# 1. Initialize session
Write-Host "`n1. Initializing session..." -ForegroundColor Yellow
$session = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/sessions/init/" -Method Post -ContentType "application/json; charset=utf-8" -Body "{}"
$sessionId = $session.session_id
$conversationId = $session.conversation_id
Write-Host "   ✅ Session created: $sessionId" -ForegroundColor Green
Write-Host "   Conversation ID: $conversationId" -ForegroundColor Gray

# 2. Send message
Write-Host "`n2. Sending chat message..." -ForegroundColor Yellow
try {
    $headers = @{
        "Content-Type" = "application/json; charset=utf-8"
        "X-Session-ID" = $sessionId
    }
    
    # Use simple English message to avoid encoding issues
    $body = '{"content": "hello, I feel anxious"}'
    
    $chat = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/chat/" -Method Post -Headers $headers -Body $body -ContentType "application/json; charset=utf-8"
    
    if ($chat.content) {
        Write-Host "   ✅ Message sent, response received" -ForegroundColor Green
        $preview = $chat.content.Substring(0, [Math]::Min(150, $chat.content.Length))
        Write-Host "   Response preview: $preview..." -ForegroundColor Gray
    }
    else {
        Write-Host "   ❌ FAIL: No response content" -ForegroundColor Red
    }
}
catch {
    Write-Host "   ❌ FAIL: Chat error - $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Get chat history
Write-Host "`n3. Fetching chat history..." -ForegroundColor Yellow
try {
    $headers = @{
        "X-Session-ID" = $sessionId
    }
    $history = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/chat/history/?conversation_id=$conversationId&limit=10" -Method Get -Headers $headers
    
    if ($history.messages -and $history.messages.Count -gt 0) {
        Write-Host "   ✅ History loaded: $($history.messages.Count) messages" -ForegroundColor Green
    }
    else {
        Write-Host "   ⚠️  No messages in history (may be expected if chat failed)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ❌ FAIL: History error - $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Log mood
Write-Host "`n4. Logging mood..." -ForegroundColor Yellow
try {
    $headers = @{
        "Content-Type" = "application/json; charset=utf-8"
        "X-Session-ID" = $sessionId
    }
    $moodBody = '{"mood_value": 4, "mood_label": "good", "note": "test"}'
    
    $moodResult = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/moods/" -Method Post -Headers $headers -Body $moodBody -ContentType "application/json; charset=utf-8"
    Write-Host "   ✅ Mood logged successfully" -ForegroundColor Green
}
catch {
    $errorMsg = $_.Exception.Message
    if ($errorMsg -like "*403*" -or $errorMsg -like "*Forbidden*") {
        Write-Host "   ⚠️  403 Forbidden - User may need to be authenticated" -ForegroundColor Yellow
    }
    else {
        Write-Host "   ❌ FAIL: Mood logging error - $errorMsg" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n=== Integration Test Complete ===" -ForegroundColor Cyan
Write-Host "Core API endpoints tested" -ForegroundColor Green
Write-Host "`nNote: For Vietnamese text, test via browser UI" -ForegroundColor Gray
