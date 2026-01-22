"""
Test Authentication APIs
Tests user registration, login, and token validation
"""
from test_utils import TestAPIClient, TestRunner, print_section
import sys


def test_auth_flow():
    """Test complete authentication flow"""
    runner = TestRunner("Authentication API Tests")
    runner.start()
    
    client = TestAPIClient()
    
    # Test data
    test_email = f"testuser_{runner.start_time.timestamp()}@example.com"
    test_password = "TestPassword123"
    test_username = "Test User"
    
    # ===== Test 1: Register New User =====
    print_section("Test 1: User Registration")
    
    response = client.post("/auth/register/", json={
        "email": test_email,
        "password": test_password,
        "username": test_username
    })
    
    runner.assert_status_code("Register - Status 201", response, 201)
    
    if response.status_code == 201:
        data = response.json()
        runner.assert_has_key("Register - Has access_token", data, "access_token")
        runner.assert_has_key("Register - Has token_type", data, "token_type")
        
        if "access_token" in data:
            client.set_token(data["access_token"])
            print(f"    Token received: {data['access_token'][:20]}...")
    
    # ===== Test 2: Get Current User =====
    print_section("Test 2: Get Current User (JWT)")
    
    response = client.get("/auth/me/")
    runner.assert_status_code("Get Me - Status 200", response, 200)
    
    if response.status_code == 200:
        data = response.json()
        runner.assert_equal("Get Me - Email matches", data.get("email"), test_email)
        runner.assert_equal("Get Me - Username matches", data.get("username"), test_username)
        runner.assert_equal("Get Me - Role is USER", data.get("role"), "user")
        runner.assert_true("Get Me - Is active", data.get("is_active", False))
    
    # ===== Test 3: Login with Existing User =====
    print_section("Test 3: User Login")
    
    # Clear token to test login
    client.token = None
    
    response = client.post("/auth/login/", json={
        "email": test_email,
        "password": test_password
    })
    
    runner.assert_status_code("Login - Status 200", response, 200)
    
    if response.status_code == 200:
        data = response.json()
        runner.assert_has_key("Login - Has access_token", data, "access_token")
        runner.assert_has_key("Login - Has token_type", data, "token_type")
        
        # Verify token works
        client.set_token(data["access_token"])
        response = client.get("/auth/me/")
        runner.assert_status_code("Login - Token valid", response, 200)
    
    # ===== Test 4: Invalid Login =====
    print_section("Test 4: Invalid Credentials")
    
    client.token = None
    
    response = client.post("/auth/login/", json={
        "email": test_email,
        "password": "WrongPassword"
    })
    
    runner.assert_status_code("Invalid Login - Status 401", response, 401)
    
    # ===== Test 5: Unauthorized Access =====
    print_section("Test 5: Unauthorized Access")
    
    client.token = None
    
    response = client.get("/auth/me/")
    runner.assert_status_code("No Token - Status 403", response, 403)
    
    # Print summary
    success = runner.finish()
    return success


if __name__ == "__main__":
    try:
        success = test_auth_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
