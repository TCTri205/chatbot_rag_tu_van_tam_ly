# Test semantic cache performance
import requests
import time

session_id = "test-cache-" + str(int(time.time()))
query = {"content": "kỹ thuật thở sâu"}

print("Testing semantic cache...")

# First request (cache miss)
print("\n1. First request (cache miss):")
start1 = time.time()
r1 = requests.post('http://localhost:8000/api/v1/chat/', 
    json=query,
    headers={"X-Session-ID": session_id})
latency1 = time.time() - start1
print(f"   Latency: {latency1:.2f}s")

# Wait a bit
time.sleep(1)

# Second request (cache hit)
print("\n2. Second request (cache hit):")
start2 = time.time()
r2 = requests.post('http://localhost:8000/api/v1/chat/', 
    json=query,
    headers={"X-Session-ID": session_id})
latency2 = time.time() - start2
print(f"   Latency: {latency2:.2f}s")

# Calculate improvement
reduction = ((1 - latency2/latency1) * 100) if latency1 > 0 else 0
print(f"\n3. Results:")
print(f"   Latency reduction: {reduction:.0f}%")

# Verify cache worked
if latency2 < latency1 * 0.5:
    print(f"   ✅ PASS: Cache reduced latency significantly")
else:
    print(f"   ⚠️  WARNING: Cache may not be working optimally")
    print(f"   (Expected >50% reduction, got {reduction:.0f}%)")

print("\nCheck Docker logs for 'Cache HIT' message:")
print("docker-compose logs backend --tail=30 | Select-String 'Cache'")
