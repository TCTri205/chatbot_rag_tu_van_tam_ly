"""
Quick diagnostic script to test endpoints
"""
import requests

base_url = "http://localhost:8080"

# Test endpoints
endpoints = [
    "/api/health/",
    "/api/v1/docs",
    "/api/v1/auth/register/",
    "/api/v1/sessions/init/",
]

print("Testing endpoints...")
print("=" * 60)

for endpoint in endpoints:
    url = base_url + endpoint
    try:
        response = requests.get(url, timeout=2)
        print(f"\n{endpoint}")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            try:
                print(f"  Response: {response.json()}")
            except:
                print(f"  Response: {response.text[:100]}")
    except Exception as e:
        print(f"\n{endpoint}")
        print(f"  Error: {e}")

print("\n" + "=" * 60)
