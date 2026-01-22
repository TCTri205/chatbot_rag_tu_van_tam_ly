"""
Test Helper Utilities
Provides common test functions and API client for manual testing
"""
import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime


class TestAPIClient:
    """Simple API client for testing without pytest"""
    
    def __init__(self, base_url: str = "http://localhost:8080/api/v1"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.session_id: Optional[str] = None
        self.conversation_id: Optional[str] = None
        
    def set_token(self, token: str):
        """Set authentication token"""
        self.token = token
        
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token if available"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.session_id:
            headers["X-Session-ID"] = self.session_id
        return headers
    
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        headers = self.get_headers()
        headers.update(kwargs.pop("headers", {}))
        
        response = requests.request(method, url, headers=headers, **kwargs)
        return response
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET request"""
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """POST request"""
        return self.request("POST", endpoint, **kwargs)
    
    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        """PATCH request"""
        return self.request("PATCH", endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE request"""
        return self.request("DELETE", endpoint, **kwargs)


class TestResult:
    """Test result container"""
    
    def __init__(self, name: str, passed: bool, message: str = "", details: Any = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details
        self.timestamp = datetime.now()
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        msg = f"{status} - {self.name}"
        if self.message:
            msg += f"\n    {self.message}"
        if self.details:
            msg += f"\n    Details: {self.details}"
        return msg


class TestRunner:
    """Simple test runner for manual tests"""
    
    def __init__(self, name: str):
        self.name = name
        self.results = []
        self.start_time = None
        self.end_time = None
        
    def start(self):
        """Start test run"""
        self.start_time = datetime.now()
        print(f"\n{'='*60}")
        print(f"Running Test Suite: {self.name}")
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
    def add_result(self, result: TestResult):
        """Add test result"""
        self.results.append(result)
        print(result)
        
    def assert_equal(self, name: str, actual: Any, expected: Any) -> TestResult:
        """Assert two values are equal"""
        passed = actual == expected
        message = f"Expected: {expected}, Got: {actual}" if not passed else ""
        result = TestResult(name, passed, message)
        self.add_result(result)
        return result
        
    def assert_true(self, name: str, condition: bool, message: str = "") -> TestResult:
        """Assert condition is true"""
        result = TestResult(name, condition, message)
        self.add_result(result)
        return result
        
    def assert_status_code(self, name: str, response: requests.Response, expected_code: int) -> TestResult:
        """Assert response status code"""
        passed = response.status_code == expected_code
        message = f"Expected: {expected_code}, Got: {response.status_code}"
        if not passed:
            message += f"\nResponse: {response.text[:200]}"
        result = TestResult(name, passed, message if not passed else "")
        self.add_result(result)
        return result
        
    def assert_has_key(self, name: str, data: Dict, key: str) -> TestResult:
        """Assert dictionary has key"""
        passed = key in data
        message = f"Key '{key}' not found in response" if not passed else ""
        result = TestResult(name, passed, message)
        self.add_result(result)
        return result
        
    def finish(self):
        """Finish test run and print summary"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        
        print(f"\n{'='*60}")
        print(f"Test Summary: {self.name}")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Duration: {duration:.2f}s")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        print(f"{'='*60}\n")
        
        return failed == 0


def print_section(title: str):
    """Print section header"""
    print(f"\n{'-'*60}")
    print(f"  {title}")
    print(f"{'-'*60}")
