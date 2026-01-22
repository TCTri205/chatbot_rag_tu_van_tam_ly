"""
Test Runner - Execute all test suites
Run with: python tests/run_all_tests.py
"""
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_auth import test_auth_flow
from test_chat import test_chat_flow


def check_backend_health():
    """Check if backend is accessible before running tests"""
    import requests
    
    base_url = "http://localhost:8080"
    
    try:
        response = requests.get(f"{base_url}/api/health/", timeout=5)
        if response.status_code == 200:
            return True
    except:
        pass
    
    print("\n" + "="*70)
    print("❌ LỖI: BACKEND CHƯA CHẠY")
    print("="*70)
    print(f"Không thể kết nối tới backend tại: {base_url}")
    print("\n💡 Vui lòng làm theo các bước sau:")
    print("\n1. Kiểm tra Docker đang chạy:")
    print("   > docker ps")
    print("\n2. Khởi động backend (nếu chưa chạy):")
    print("   > docker-compose up -d")
    print("\n3. Đợi ~10 giây để backend khởi động hoàn toàn")
    print("\n4. Kiểm tra backend health:")
    print(f"   > curl {base_url}/api/health/")
    print("\n5. Chạy lại tests:")
    print("   > python tests/run_all_tests.py")
    print("="*70 + "\n")
    return False


def main():
    """Run all test suites"""
    print("\n" + "="*70)
    print(" "*20 + "CHATBOT TÂM LÝ - TEST SUITE")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: http://localhost:8080/api/v1")
    print("="*70 + "\n")
    
    # Check backend health first
    if not check_backend_health():
        sys.exit(1)
    
    results = {}
    
    # Run test suites
    test_suites = [
        ("Authentication", test_auth_flow),
        ("Chat & Sessions", test_chat_flow),
    ]
    
    for name, test_func in test_suites:
        try:
            print(f"\n{'#'*70}")
            print(f"# Running: {name}")
            print(f"{'#'*70}")
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    # Print final summary
    print("\n" + "="*70)
    print(" "*25 + "FINAL SUMMARY")
    print("="*70)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"\nTotal Suites: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    print("="*70 + "\n")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
