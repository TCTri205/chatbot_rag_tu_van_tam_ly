"""
Verification Script for Authentication Bug Fixes
Tests all fixed issues to ensure proper functionality
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8080"
API_V1 = f"{BASE_URL}/api/v1"


class Color:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_test(name: str, passed: bool, details: str = ""):
    """Pretty print test results"""
    status = f"{Color.GREEN}✅ PASS{Color.END}" if passed else f"{Color.RED}❌ FAIL{Color.END}"
    print(f"\n{status} {Color.BLUE}{name}{Color.END}")
    if details:
        print(f"  → {details}")


def test_health_check() -> bool:
    """Test 1: Health endpoint is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/api/health/", timeout=5)
        passed = response.status_code == 200
        details = f"Status: {response.status_code}"
        if passed:
            data = response.json()
            details += f" | DB: {data.get('services', {}).get('database', 'unknown')}"
        print_test("Health Check", passed, details)
        return passed
    except Exception as e:
        print_test("Health Check", False, f"Error: {str(e)}")
        return False


def test_invalid_email_format() -> bool:
    """Test 2: Register with invalid email returns proper 422 error"""
    try:
        response = requests.post(
            f"{API_V1}/auth/register/",
            json={
                "email": "bad-email",
                "username": "testuser",
                "password": "12345678"
            },
            timeout=5
        )
        
        passed = response.status_code == 422
        
        if passed:
            error_data = response.json()
            # Check if detail is an array (FastAPI validation error format)
            has_array_detail = isinstance(error_data.get('detail'), list)
            
            if has_array_detail:
                errors = error_data['detail']
                error_msg = ', '.join([f"{err['loc'][-1]}: {err['msg']}" for err in errors])
                details = f"422 Validation Error | {error_msg}"
            else:
                details = f"422 but unexpected format: {error_data}"
                passed = False
        else:
            details = f"Status: {response.status_code} (Expected 422)"
            passed = False
            
        print_test("Invalid Email Format Validation", passed, details)
        return passed
        
    except Exception as e:
        print_test("Invalid Email Format Validation", False, f"Error: {str(e)}")
        return False


def test_short_password() -> bool:
    """Test 3: Register with short password returns proper 422 error"""
    try:
        response = requests.post(
            f"{API_V1}/auth/register/",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "123"  # Too short
            },
            timeout=5
        )
        
        passed = response.status_code == 422
        
        if passed:
            error_data = response.json()
            has_array_detail = isinstance(error_data.get('detail'), list)
            
            if has_array_detail:
                errors = error_data['detail']
                # Check if password length error is present
                password_error = any('password' in str(err.get('loc', [])) for err in errors)
                
                if password_error:
                    error_msg = ', '.join([f"{err['loc'][-1]}: {err['msg']}" for err in errors])
                    details = f"422 Validation Error | {error_msg}"
                else:
                    details = "422 but password error not found"
                    passed = False
            else:
                details = f"422 but unexpected format: {error_data}"
                passed = False
        else:
            details = f"Status: {response.status_code} (Expected 422)"
            passed = False
            
        print_test("Short Password Validation", passed, details)
        return passed
        
    except Exception as e:
        print_test("Short Password Validation", False, f"Error: {str(e)}")
        return False


def test_sql_injection_protection() -> bool:
    """Test 4: SQL injection attempt is blocked"""
    try:
        response = requests.post(
            f"{API_V1}/auth/login/",
            json={
                "email": "' OR 1=1 --",
                "password": "anything"
            },
            timeout=5
        )
        
        # Should return 422 (invalid email) or 401 (not found), never succeed
        passed = response.status_code in [422, 401]
        details = f"Status: {response.status_code} | SQL injection blocked"
        
        print_test("SQL Injection Protection", passed, details)
        return passed
        
    except Exception as e:
        print_test("SQL Injection Protection", False, f"Error: {str(e)}")
        return False


def test_login_wrong_credentials() -> bool:
    """Test 5: Login with wrong credentials returns 401"""
    try:
        response = requests.post(
            f"{API_V1}/auth/login/",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            },
            timeout=5
        )
        
        passed = response.status_code == 401
        
        if passed:
            error_data = response.json()
            detail = error_data.get('detail', '')
            details = f"401 Unauthorized | Message: '{detail}'"
        else:
            details = f"Status: {response.status_code} (Expected 401)"
            
        print_test("Wrong Login Credentials", passed, details)
        return passed
        
    except Exception as e:
        print_test("Wrong Login Credentials", False, f"Error: {str(e)}")
        return False


def test_email_already_registered() -> bool:
    """Test 6: Register with existing email returns 400"""
    # First, try to register a user
    try:
        # Try to register twice with same email
        email = "duplicate@example.com"
        user_data = {
            "email": email,
            "username": "testuser1",
            "password": "password123"
        }
        
        # First registration
        response1 = requests.post(f"{API_V1}/auth/register/", json=user_data, timeout=5)
        
        # Second registration with same email
        user_data["username"] = "testuser2"
        response2 = requests.post(f"{API_V1}/auth/register/", json=user_data, timeout=5)
        
        # Second should fail with 400
        passed = response2.status_code == 400
        
        if passed:
            error_data = response2.json()
            details = f"400 Bad Request | {error_data.get('detail', '')}"
        else:
            details = f"Status: {response2.status_code} (Expected 400)"
            
        print_test("Duplicate Email Prevention", passed, details)
        return passed
        
    except Exception as e:
        print_test("Duplicate Email Prevention", False, f"Error: {str(e)}")
        return False


def main():
    """Run all verification tests"""
    print(f"\n{Color.YELLOW}{'='*60}")
    print("🧪 Authentication Bug Fix Verification")
    print(f"{'='*60}{Color.END}\n")
    
    print(f"{Color.BLUE}Testing against: {BASE_URL}{Color.END}")
    print(f"{Color.BLUE}API Version: v1{Color.END}\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Invalid Email Validation", test_invalid_email_format),
        ("Short Password Validation", test_short_password),
        ("SQL Injection Protection", test_sql_injection_protection),
        ("Wrong Login Credentials", test_login_wrong_credentials),
        ("Duplicate Email Prevention", test_email_already_registered),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n{Color.RED}❌ CRITICAL ERROR in {name}: {str(e)}{Color.END}")
            results.append((name, False))
    
    # Summary
    print(f"\n{Color.YELLOW}{'='*60}")
    print("📊 Test Summary")
    print(f"{'='*60}{Color.END}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Color.GREEN}✅" if result else f"{Color.RED}❌"
        print(f"{status} {name}{Color.END}")
    
    print(f"\n{Color.BLUE}Results: {passed}/{total} tests passed{Color.END}")
    
    if passed == total:
        print(f"\n{Color.GREEN}✅ ALL TESTS PASSED! Bug fixes verified.{Color.END}\n")
        return 0
    else:
        print(f"\n{Color.RED}❌ Some tests failed. Please review the fixes.{Color.END}\n")
        return 1


if __name__ == "__main__":
    exit(main())
