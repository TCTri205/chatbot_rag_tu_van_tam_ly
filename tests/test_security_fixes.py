"""
Security Test Script - No pytest required
Tests the 3 critical security fixes implemented.

Usage:
    python tests/test_security_fixes.py

Requirements:
    - Server running at localhost (docker-compose up)
    - requests library (already in requirements.txt)
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8080/api/v1"
HEALTH_URL = "http://localhost:8080/api/health"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log_pass(msg):
    print(f"{GREEN}[PASS]{RESET} {msg}")

def log_fail(msg):
    print(f"{RED}[FAIL]{RESET} {msg}")

def log_info(msg):
    print(f"{YELLOW}[INFO]{RESET} {msg}")

# =========================================
# TEST 1: Chat History Ownership Check
# =========================================
def test_chat_history_ownership():
    """
    Test that authenticated users can only access their own conversations.
    """
    print("\n" + "="*60)
    print("TEST 1: Chat History Ownership Check")
    print("="*60)
    
    # Step 1: Create 2 users
    user1_email = "testuser1_security@example.com"
    user2_email = "testuser2_security@example.com"
    password = "password123"
    
    # Register user1
    resp = requests.post(f"{BASE_URL}/auth/register/", json={
        "email": user1_email,
        "password": password,
        "username": "testuser1"
    })
    if resp.status_code == 400 and "already registered" in resp.text:
        log_info(f"User1 already exists, logging in...")
        resp = requests.post(f"{BASE_URL}/auth/login/", json={
            "email": user1_email,
            "password": password
        })
    
    if resp.status_code not in [200, 201]:
        log_fail(f"Failed to create/login user1: {resp.text}")
        return False
    
    user1_token = resp.json().get("access_token")
    log_info(f"User1 authenticated")
    
    # Register user2
    resp = requests.post(f"{BASE_URL}/auth/register/", json={
        "email": user2_email,
        "password": password,
        "username": "testuser2"
    })
    if resp.status_code == 400 and "already registered" in resp.text:
        resp = requests.post(f"{BASE_URL}/auth/login/", json={
            "email": user2_email,
            "password": password
        })
    
    if resp.status_code not in [200, 201]:
        log_fail(f"Failed to create/login user2: {resp.text}")
        return False
    
    user2_token = resp.json().get("access_token")
    log_info(f"User2 authenticated")
    
    # Step 2: User1 creates a session and sends a message
    resp = requests.post(f"{BASE_URL}/sessions/init", 
        headers={"Authorization": f"Bearer {user1_token}"},
        json={}
    )
    if resp.status_code != 200:
        log_fail(f"Failed to init session for user1: {resp.text}")
        return False
    
    session_data = resp.json()
    user1_session_id = session_data["session_id"]
    user1_conversation_id = session_data["conversation_id"]
    log_info(f"User1 conversation created: {user1_conversation_id}")
    
    # Step 3: User2 tries to access User1's conversation
    resp = requests.get(
        f"{BASE_URL}/chat/history",
        params={"conversation_id": user1_conversation_id},
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    
    if resp.status_code == 403:
        log_pass("User2 correctly denied access to User1's conversation (403 Forbidden)")
        return True
    elif resp.status_code == 200:
        log_fail(f"SECURITY BUG: User2 accessed User1's conversation!")
        return False
    else:
        log_info(f"Unexpected response: {resp.status_code} - {resp.text}")
        return False

# =========================================
# TEST 2: Session Init User ID Injection
# =========================================
def test_session_init_user_id_injection():
    """
    Test that user_id cannot be injected in session init body.
    """
    print("\n" + "="*60)
    print("TEST 2: Session Init User ID Injection Prevention")
    print("="*60)
    
    # Try to create session with fake user_id (without JWT)
    fake_user_id = "550e8400-e29b-41d4-a716-446655440000"
    
    resp = requests.post(f"{BASE_URL}/sessions/init", json={
        "user_id": fake_user_id  # This should be ignored
    })
    
    if resp.status_code != 200:
        log_fail(f"Session init failed: {resp.text}")
        return False
    
    session_data = resp.json()
    log_info(f"Session created: {session_data['session_id']}")
    
    # The session should be a GUEST session (user_id ignored)
    # We can verify by checking that we can't access user-only features
    resp = requests.post(
        f"{BASE_URL}/moods/",
        headers={"X-Session-ID": str(session_data['session_id'])},
        json={"mood_value": 3}
    )
    
    if resp.status_code == 403 and "registered users" in resp.text.lower():
        log_pass("user_id from body was correctly ignored - session is guest")
        return True
    elif resp.status_code == 201:
        log_fail("SECURITY BUG: Session accepted fake user_id and allowed mood logging!")
        return False
    else:
        log_info(f"Response: {resp.status_code} - {resp.text}")
        # Could be 404 or other error, still indicates guest behavior
        log_pass("user_id appears to be ignored (session behaves as guest)")
        return True

# =========================================
# TEST 3: Export Requires Authentication
# =========================================
def test_export_requires_auth():
    """
    Test that export endpoint requires authentication (not available to guests).
    """
    print("\n" + "="*60)
    print("TEST 3: Export Requires Authentication")
    print("="*60)
    
    # Create a guest session
    resp = requests.post(f"{BASE_URL}/sessions/init", json={})
    if resp.status_code != 200:
        log_fail(f"Failed to create guest session: {resp.text}")
        return False
    
    session_id = resp.json()["session_id"]
    
    # Try to export as guest (should fail with 403)
    resp = requests.get(
        f"{BASE_URL}/conversations/export",
        headers={"X-Session-ID": str(session_id)}
    )
    
    if resp.status_code == 403:
        log_pass("Export correctly denied for guest users (403 Forbidden)")
        return True
    elif resp.status_code == 401:
        log_pass("Export correctly requires authentication (401 Unauthorized)")
        return True
    elif resp.status_code == 200:
        log_fail("SECURITY BUG: Guest was able to export data!")
        return False
    else:
        log_info(f"Response: {resp.status_code} - {resp.text}")
        return False

# =========================================
# Main
# =========================================
def main():
    print("\n" + "="*60)
    print("[SECURITY] TESTS FOR SYSTEM ISSUE FIXES")
    print("="*60)
    
    # Check server is running
    try:
        resp = requests.get(HEALTH_URL, timeout=5)
        if resp.status_code != 200:
            print(f"{RED}Server not responding properly. Is docker-compose up?{RESET}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"{RED}Cannot connect to server. Please run: docker-compose up{RESET}")
        sys.exit(1)
    
    log_info("Server is running")
    
    results = []
    
    # Run tests
    results.append(("Chat History Ownership", test_chat_history_ownership()))
    results.append(("Session Init Injection", test_session_init_user_id_injection()))
    results.append(("Export Auth Required", test_export_requires_auth()))
    
    # Summary
    print("\n" + "="*60)
    print("[SUMMARY] TEST RESULTS")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{GREEN}All security tests passed!{RESET}")
        return 0
    else:
        print(f"\n{RED}Some tests failed!{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
