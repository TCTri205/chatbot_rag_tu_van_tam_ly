"""
Backend Health Check
Quick script to verify backend is running before tests
"""
import requests
import sys


def check_backend(base_url: str = "http://localhost:8080"):
    """
    Check if backend is accessible
    
    Args:
        base_url: Base URL of backend (without /api/v1)
    
    Returns:
        bool: True if backend is up, False otherwise
    """
    try:
        # Try health endpoint
        response = requests.get(f"{base_url}/api/health/", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Backend is UP: {base_url}")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"⚠️  Backend responded but with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Backend is DOWN: {base_url}")
        print(f"\n💡 Làm theo các bước sau:")
        print(f"   1. Kiểm tra Docker đang chạy:")
        print(f"      > docker ps")
        print(f"\n   2. Khởi động backend:")
        print(f"      > docker-compose up -d")
        print(f"\n   3. Đợi ~10s để backend khởi động hoàn toàn")
        print(f"\n   4. Chạy lại tests:")
        print(f"      > python tests/run_all_tests.py")
        return False
        
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra backend: {e}")
        return False


if __name__ == "__main__":
    # Allow custom URL from command line
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    is_up = check_backend(base_url)
    sys.exit(0 if is_up else 1)
