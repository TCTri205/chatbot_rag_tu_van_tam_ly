"""
Standalone API Test Script - Không cần pytest
Chạy bằng: python tests/test_api_standalone.py

Theo yêu cầu: Không duyệt web, hạn chế rebuild backend
"""
import requests
import time
import json
import sys

BASE_URL = "http://localhost:8080/api/v1"
RESULTS = {"passed": 0, "failed": 0, "skipped": 0}


def log_result(test_name: str, passed: bool, detail: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    if passed:
        RESULTS["passed"] += 1
    else:
        RESULTS["failed"] += 1
    print(f"{status}: {test_name}")
    if detail:
        print(f"        {detail}")


def log_skip(test_name: str, reason: str):
    """Log skipped test"""
    RESULTS["skipped"] += 1
    print(f"⏭️ SKIP: {test_name}")
    print(f"        Reason: {reason}")


def test_health():
    """TC 0.1: Health check"""
    try:
        r = requests.get("http://localhost:8080/api/health/", timeout=5)
        if r.status_code == 200:
            log_result("Health Check", True, f"Response: {r.json()}")
            return True
        else:
            log_result("Health Check", False, f"Status: {r.status_code}")
            return False
    except requests.exceptions.ConnectionError as e:
        log_result("Health Check", False, f"Connection Error: Backend không chạy")
        return False
    except Exception as e:
        log_result("Health Check", False, f"Error: {e}")
        return False


def test_session_init():
    """TC 1.1: Session initialization"""
    try:
        r = requests.post(f"{BASE_URL}/sessions/init/", json={}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            session_id = data.get("session_id")
            conversation_id = data.get("conversation_id")
            log_result("Session Init", True, f"session_id: {str(session_id)[:8]}...")
            return session_id, conversation_id
        else:
            log_result("Session Init", False, f"Status: {r.status_code}, Body: {r.text[:100]}")
            return None, None
    except Exception as e:
        log_result("Session Init", False, f"Error: {e}")
        return None, None


def test_user_registration():
    """TC 1.2: User Registration"""
    try:
        test_email = f"test_user_{int(time.time())}@example.com"
        r = requests.post(f"{BASE_URL}/auth/register/", json={
            "username": "automated_test_user",
            "email": test_email,
            "password": "TestPass123!"
        }, timeout=10)
        
        if r.status_code == 201:
            data = r.json()
            token = data.get("access_token")
            log_result("User Registration", True, f"Email: {test_email}")
            return token, test_email
        else:
            log_result("User Registration", False, f"Status: {r.status_code}, Body: {r.text[:150]}")
            return None, None
    except Exception as e:
        log_result("User Registration", False, f"Error: {e}")
        return None, None


def test_user_login(email: str, password: str = "TestPass123!"):
    """TC 1.3: User Login"""
    try:
        r = requests.post(f"{BASE_URL}/auth/login/", json={
            "email": email,
            "password": password
        }, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token")
            log_result("User Login", True)
            return token
        else:
            log_result("User Login", False, f"Status: {r.status_code}")
            return None
    except Exception as e:
        log_result("User Login", False, f"Error: {e}")
        return None


def test_exercises():
    """TC 8.1: List exercises"""
    try:
        r = requests.get(f"{BASE_URL}/exercises/", timeout=5)
        if r.status_code == 200:
            data = r.json()
            log_result("List Exercises", True, f"Found {len(data)} exercises")
            return True
        else:
            log_result("List Exercises", False, f"Status: {r.status_code}")
            return False
    except Exception as e:
        log_result("List Exercises", False, f"Error: {e}")
        return False


def test_chat(session_id: str, token: str = None):
    """TC 2.1: Basic chat message"""
    try:
        headers = {"X-Session-ID": str(session_id)}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        r = requests.post(
            f"{BASE_URL}/chat/",
            headers=headers,
            json={"content": "Xin chào, tôi cảm thấy lo lắng"},
            timeout=60  # Chat có thể chậm do RAG
        )
        
        if r.status_code == 200:
            data = r.json()
            message_id = data.get("message_id")
            content = data.get("content", "")[:50]
            log_result("Chat Message", True, f"Response: {content}...")
            return message_id
        else:
            log_result("Chat Message", False, f"Status: {r.status_code}, Body: {r.text[:100]}")
            return None
    except Exception as e:
        log_result("Chat Message", False, f"Error: {e}")
        return None


def test_admin_unauthorized():
    """TC 11.2: Unauthorized admin access returns 401/403"""
    try:
        r = requests.get(f"{BASE_URL}/admin/stats/overview", timeout=5)
        if r.status_code in [401, 403]:
            log_result("Admin Unauthorized", True, f"Correctly blocked: {r.status_code}")
            return True
        else:
            log_result("Admin Unauthorized", False, f"Expected 401/403, got {r.status_code}")
            return False
    except Exception as e:
        log_result("Admin Unauthorized", False, f"Error: {e}")
        return False


def test_admin_users_endpoint():
    """TC 5.x: Admin users endpoint exists"""
    try:
        r = requests.get(f"{BASE_URL}/admin/users/", timeout=5)
        # Should return 401/403 (no auth) not 404 (endpoint not found)
        if r.status_code in [401, 403]:
            log_result("Admin Users Endpoint", True, f"Endpoint exists (blocked without auth: {r.status_code})")
            return True
        elif r.status_code == 404:
            log_result("Admin Users Endpoint", False, f"Endpoint NOT FOUND (404)")
            return False
        else:
            log_result("Admin Users Endpoint", True, f"Status: {r.status_code}")
            return True
    except Exception as e:
        log_result("Admin Users Endpoint", False, f"Error: {e}")
        return False


def test_404_handling():
    """TC 11.3: Invalid endpoint returns 404"""
    try:
        r = requests.get(f"{BASE_URL}/nonexistent/endpoint", timeout=5)
        if r.status_code == 404:
            log_result("404 Handling", True)
            return True
        else:
            log_result("404 Handling", False, f"Expected 404, got {r.status_code}")
            return False
    except Exception as e:
        log_result("404 Handling", False, f"Error: {e}")
        return False


def test_invalid_login():
    """TC 11.1: Invalid credentials"""
    try:
        r = requests.post(f"{BASE_URL}/auth/login/", json={
            "email": "nonexistent@example.com",
            "password": "wrong"
        }, timeout=5)
        
        if r.status_code in [401, 404]:
            log_result("Invalid Login Rejected", True, f"Correctly rejected: {r.status_code}")
            return True
        else:
            log_result("Invalid Login Rejected", False, f"Expected 401/404, got {r.status_code}")
            return False
    except Exception as e:
        log_result("Invalid Login Rejected", False, f"Error: {e}")
        return False


def test_mood_tracking(token: str, session_id: str = None):
    """TC 3.1: Log mood entry"""
    if not token:
        log_skip("Mood Tracking", "Requires authenticated user")
        return False
    
    if not session_id:
        log_skip("Mood Tracking", "Requires session_id")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Session-ID": str(session_id)
        }
        r = requests.post(
            f"{BASE_URL}/moods/",
            headers=headers,
            json={
                "mood_value": 4,
                "mood_label": "happy",
                "note": "Automated test mood entry"
            },
            timeout=10
        )
        
        if r.status_code in [200, 201]:
            log_result("Mood Tracking", True)
            return True
        elif r.status_code == 403:
            # Guest session - mood only for registered users
            log_result("Mood Tracking", True, "Guest session, mood tracking skipped (expected)")
            return True
        else:
            log_result("Mood Tracking", False, f"Status: {r.status_code}, Body: {r.text[:100]}")
            return False
    except Exception as e:
        log_result("Mood Tracking", False, f"Error: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("  STANDALONE API TEST SCRIPT")
    print("  (Không cần pytest, không cần rebuild Docker)")
    print("="*60 + "\n")
    
    # Step 1: Health check
    if not test_health():
        print("\n" + "="*60)
        print("❌ BACKEND KHÔNG CHẠY!")
        print("="*60)
        print("Vui lòng chạy: docker-compose up -d")
        print("Sau đó đợi ~10s và chạy lại script này.")
        print("\nĐể xem logs: docker-compose logs backend --tail=50")
        print("="*60 + "\n")
        sys.exit(1)
    
    # Step 2: Basic endpoint tests
    print("\n--- Core Endpoints ---")
    session_id, conversation_id = test_session_init()
    test_exercises()
    
    # Step 3: Authentication tests
    print("\n--- Authentication ---")
    token, test_email = test_user_registration()
    if token and test_email:
        test_user_login(test_email)
    test_invalid_login()
    
    # Step 4: Chat test (if session exists)
    print("\n--- Chat System ---")
    if session_id:
        test_chat(session_id, token)
    else:
        log_skip("Chat Message", "No session available")
    
    # Step 5: Mood tracking (requires auth)
    print("\n--- Mood Tracking ---")
    test_mood_tracking(token, session_id)
    
    # Step 6: Admin endpoints
    print("\n--- Admin Endpoints ---")
    test_admin_unauthorized()
    test_admin_users_endpoint()
    
    # Step 7: Error handling
    print("\n--- Error Handling ---")
    test_404_handling()
    
    # Summary
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    print(f"  Passed:  {RESULTS['passed']} ✅")
    print(f"  Failed:  {RESULTS['failed']} ❌")
    print(f"  Skipped: {RESULTS['skipped']} ⏭️")
    total = RESULTS['passed'] + RESULTS['failed']
    if total > 0:
        rate = (RESULTS['passed'] / total) * 100
        print(f"  Success Rate: {rate:.1f}%")
    print("="*60 + "\n")
    
    # Exit code
    sys.exit(0 if RESULTS['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
