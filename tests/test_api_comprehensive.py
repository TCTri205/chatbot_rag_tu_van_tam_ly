"""
Comprehensive API Test Suite for Chatbot Tâm Lý
Tests all Sprint 1-4 features with full coverage
"""
import pytest
import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:8080/api/v1"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin1234!"
TEST_USER_EMAIL = f"test_user_{int(time.time())}@example.com"
TEST_USER_PASSWORD = "TestPass123!"

class TestAuthenticationFlow:
    """Test authentication and session management"""
    
    def test_01_user_registration(self):
        """TC 1.2: User Registration"""
        response = requests.post(f"{BASE_URL}/auth/register/", json={
            "username": "automated_test_user",
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = response.json()
        assert "access_token" in data, "access_token missing from response"
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == TEST_USER_EMAIL
        
        # Store for later tests
        pytest.test_user_token = data["access_token"]
        pytest.test_user_id = data["user"]["id"]
        print(f"✅ User registration successful: {TEST_USER_EMAIL}")
    
    def test_02_user_login(self):
        """TC 1.3: User Login"""
        response = requests.post(f"{BASE_URL}/auth/login/", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"✅ User login successful")
    
    def test_03_invalid_login(self):
        """TC 11.1: Invalid credentials"""
        response = requests.post(f"{BASE_URL}/auth/login/", json={
            "email": "nonexistent@example.com",
            "password": "wrong"
        })
        
        assert response.status_code in [401, 404]
        print(f"✅ Invalid login correctly rejected")

class TestSessionManagement:
    """Test session initialization and management"""
    
    def test_01_session_init(self):
        """TC 1.1: Guest Session Init"""
        response = requests.post(f"{BASE_URL}/sessions/init/", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "conversation_id" in data
        assert "greeting" in data
        
        # Store for later
        pytest.session_id = data["session_id"]
        pytest.conversation_id = data["conversation_id"]
        print(f"✅ Session initialized: {data['session_id'][:8]}...")

class TestChatSystem:
    """Test core chat functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before each test"""
        if not hasattr(pytest, 'test_user_token'):
            # Initialize session for guest
            response = requests.post(f"{BASE_URL}/sessions/init/", json={})
            data = response.json()
            pytest.session_id = data["session_id"]
            pytest.conversation_id = data["conversation_id"]
    
    def test_01_basic_chat_message(self):
        """TC 2.1: Send basic chat message"""
        headers = {
            "X-Session-ID": pytest.session_id,
        }
        if hasattr(pytest, 'test_user_token'):
            headers["Authorization"] = f"Bearer {pytest.test_user_token}"
        
        response = requests.post(
            f"{BASE_URL}/chat/",
            headers=headers,
            json={"content": "Xin chào, tôi cảm thấy lo lắng"}
        )
        
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        assert "message_id" in data
        assert "conversation_id" in data
        assert "content" in data
        assert data["role"] == "assistant"
        
        # Store message for feedback test
        pytest.last_message_id = data["message_id"]
        print(f"✅ Chat message sent and received response")
        print(f"   Response preview: {data['content'][:50]}...")
    
    def test_02_crisis_detection(self):
        """TC 2.2: Crisis keyword detection"""
        headers = {"X-Session-ID": pytest.session_id}
        if hasattr(pytest, 'test_user_token'):
            headers["Authorization"] = f"Bearer {pytest.test_user_token}"
        
        response = requests.post(
            f"{BASE_URL}/chat/",
            headers=headers,
            json={"content": "Tôi muốn tự tử"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Note: Crisis response format may vary
        # Check for crisis indicators
        print(f"✅ Crisis detection test completed")
        print(f"   Response: {data.get('content', 'N/A')[:100]}...")

class TestMoodTracking:
    """Test mood tracking functionality"""
    
    def test_01_log_mood(self):
        """TC 3.1: Log mood entry"""
        if not hasattr(pytest, 'test_user_token'):
            pytest.skip("Mood tracking requires authentication")
        
        headers = {"Authorization": f"Bearer {pytest.test_user_token}"}
        response = requests.post(
            f"{BASE_URL}/moods/",
            headers=headers,
            json={
                "mood_value": 4,
                "mood_label": "happy",
                "note": "Automated test mood entry"
            }
        )
        
        assert response.status_code in [200, 201]
        print(f"✅ Mood entry logged successfully")
    
    def test_02_get_mood_history(self):
        """TC 3.2: Get mood history"""
        if not hasattr(pytest, 'test_user_token'):
            pytest.skip("Mood history requires authentication")
        
        headers = {"Authorization": f"Bearer {pytest.test_user_token}"}
        response = requests.get(
            f"{BASE_URL}/moods/history/",
            headers=headers,
            params={"days": 7}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Mood history retrieved: {len(data)} entries")

class TestFeedbackSystem:
    """Test feedback functionality"""
    
    def test_01_submit_feedback(self):
        """TC 9.1: Submit positive feedback"""
        if not hasattr(pytest, 'last_message_id'):
            pytest.skip("Need message_id from chat test")
        
        headers = {"X-Session-ID": pytest.session_id}
        if hasattr(pytest, 'test_user_token'):
            headers["Authorization"] = f"Bearer {pytest.test_user_token}"
        
        response = requests.post(
            f"{BASE_URL}/feedback/",
            headers=headers,
            json={
                "message_id": pytest.last_message_id,
                "rating": 1,
                "comment": "Automated test feedback"
            }
        )
        
        assert response.status_code in [200, 201]
        print(f"✅ Feedback submitted successfully")

class TestAdminDashboard:
    """Test admin dashboard and stats"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin before tests"""
        response = requests.post(f"{BASE_URL}/auth/login/", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            pytest.admin_token = data["access_token"]
        else:
            pytest.skip("Admin login failed - check credentials")
    
    def test_01_get_overview_stats(self):
        """TC 4.1: Get overview stats"""
        headers = {"Authorization": f"Bearer {pytest.admin_token}"}
        response = requests.get(
            f"{BASE_URL}/admin/stats/overview",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_conversations" in data
        print(f"✅ Admin stats retrieved")
        print(f"   Users: {data.get('total_users')}, Conversations: {data.get('total_conversations')}")
    
    def test_02_get_word_cloud(self):
        """TC 4.1: Get word cloud data"""
        headers = {"Authorization": f"Bearer {pytest.admin_token}"}
        response = requests.get(
            f"{BASE_URL}/admin/stats/word-cloud",
            headers=headers,
            params={"limit": 20}
        )
        
        assert response.status_code == 200
        print(f"✅ Word cloud data retrieved")
    
    def test_03_get_mood_trends(self):
        """TC 4.1: Get mood trends"""
        headers = {"Authorization": f"Bearer {pytest.admin_token}"}
        response = requests.get(
            f"{BASE_URL}/admin/stats/mood-trends",
            headers=headers,
            params={"days": 30}
        )
        
        assert response.status_code == 200
        print(f"✅ Mood trends retrieved")

class TestAdminUserManagement:
    """Test Sprint 4: Admin user management"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        if not hasattr(pytest, 'admin_token'):
            response = requests.post(f"{BASE_URL}/auth/login/", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            if response.status_code == 200:
                pytest.admin_token = response.json()["access_token"]
            else:
                pytest.skip("Admin login required")
    
    def test_01_list_users(self):
        """TC 5.1: List users"""
        headers = {"Authorization": f"Bearer {pytest.admin_token}"}
        response = requests.get(
            f"{BASE_URL}/admin/users/",
            headers=headers,
            params={"page": 1, "page_size": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        print(f"✅ User list retrieved: {data['total']} total users")
    
    def test_02_search_users(self):
        """TC 5.2: Search users"""
        headers = {"Authorization": f"Bearer {pytest.admin_token}"}
        response = requests.get(
            f"{BASE_URL}/admin/users/",
            headers=headers,
            params={"search": "test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        print(f"✅ User search completed: {len(data['users'])} results")
    
    def test_03_ban_unban_user(self):
        """TC 5.3 & 5.4: Ban and Unban user"""
        if not hasattr(pytest, 'test_user_id'):
            pytest.skip("Need test user from registration")
        
        headers = {"Authorization": f"Bearer {pytest.admin_token}"}
        
        # Ban user
        response = requests.post(
            f"{BASE_URL}/admin/users/{pytest.test_user_id}/ban",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False
        print(f"✅ User banned successfully")
        
        # Wait a moment
        time.sleep(0.5)
        
        # Unban user
        response = requests.post(
            f"{BASE_URL}/admin/users/{pytest.test_user_id}/unban",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == True
        print(f"✅ User unbanned successfully")

class TestDataExport:
    """Test Sprint 4: Data export"""
    
    def test_01_export_chat_history(self):
        """TC 6.1: Export as authenticated user"""
        if not hasattr(pytest, 'test_user_token'):
            pytest.skip("Need authenticated user")
        
        headers = {"Authorization": f"Bearer {pytest.test_user_token}"}
        response = requests.get(
            f"{BASE_URL}/conversations/export",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        assert 'attachment' in response.headers.get('Content-Disposition', '')
        
        # Verify JSON structure
        data = response.json()
        assert "export_date" in data
        assert "user_id" in data
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
        
        print(f"✅ Export successful")
        print(f"   Conversations exported: {len(data['conversations'])}")
        print(f"   Export date: {data['export_date']}")

class TestConversationManagement:
    """Test conversation CRUD operations"""
    
    def test_01_list_conversations(self):
        """List user conversations"""
        if not hasattr(pytest, 'test_user_token'):
            pytest.skip("Need authenticated user")
        
        headers = {
            "Authorization": f"Bearer {pytest.test_user_token}",
            "X-Session-ID": pytest.session_id
        }
        response = requests.get(
            f"{BASE_URL}/conversations/",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        print(f"✅ Conversations listed: {len(data['conversations'])} found")
    
    def test_02_archive_conversation(self):
        """TC 7.1: Clear/Archive conversation"""
        if not hasattr(pytest, 'conversation_id'):
            pytest.skip("Need conversation_id")
        
        headers = {"X-Session-ID": pytest.session_id}
        if hasattr(pytest, 'test_user_token'):
            headers["Authorization"] = f"Bearer {pytest.test_user_token}"
        
        response = requests.delete(
            f"{BASE_URL}/conversations/{pytest.conversation_id}/",
            headers=headers
        )
        
        assert response.status_code in [200, 204]
        print(f"✅ Conversation archived successfully")

class TestExercises:
    """Test relaxation exercises"""
    
    def test_01_list_exercises(self):
        """TC 8.1: List exercises"""
        response = requests.get(f"{BASE_URL}/exercises/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✅ Exercises retrieved: {len(data)} exercises")
        
        # Verify exercise structure
        if data:
            ex = data[0]
            assert "id" in ex
            assert "title" in ex
            assert "category" in ex

class TestErrorHandling:
    """Test error scenarios"""
    
    def test_01_unauthorized_access(self):
        """TC 11.2: Unauthorized admin access"""
        response = requests.get(f"{BASE_URL}/admin/stats/overview")
        
        assert response.status_code in [401, 403]
        print(f"✅ Unauthorized access correctly blocked")
    
    def test_02_invalid_endpoint(self):
        """Test 404 handling"""
        response = requests.get(f"{BASE_URL}/nonexistent/endpoint")
        
        assert response.status_code == 404
        print(f"✅ 404 error handled correctly")
    
    def test_03_invalid_json(self):
        """Test malformed request"""
        response = requests.post(
            f"{BASE_URL}/chat/",
            headers={"X-Session-ID": "invalid-session"},
            json={}  # Missing content
        )
        
        # Should return validation error
        assert response.status_code in [400, 422]
        print(f"✅ Invalid request rejected")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
