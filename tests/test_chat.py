"""
Test Chat & Session APIs
Tests session initialization, chat messaging, and history
"""
from test_utils import TestAPIClient, TestRunner, print_section
import sys


def test_chat_flow():
    """Test complete chat flow"""
    runner = TestRunner("Chat & Session API Tests")
    runner.start()
    
    client = TestAPIClient()
    
    # ===== Test 1: Initialize Session (Guest) =====
    print_section("Test 1: Guest Session Initialization")
    
    response = client.post("/sessions/init/", json={})
    
    runner.assert_status_code("Init Session - Status 200", response, 200)
    
    if response.status_code == 200:
        data = response.json()
        runner.assert_has_key("Init - Has session_id", data, "session_id")
        runner.assert_has_key("Init - Has conversation_id", data, "conversation_id")
        runner.assert_has_key("Init - Has greeting", data, "greeting")
        
        if "session_id" in data:
            client.session_id = data["session_id"]
            client.conversation_id = data["conversation_id"]
            print(f"    Session ID: {client.session_id}")
            print(f"    Conversation ID: {client.conversation_id}")
    
    # ===== Test 2: Send Chat Message =====
    print_section("Test 2: Send Chat Message")
    
    if not client.session_id:
        print("    ⚠️  Skipping - No session ID")
    else:
        response = client.post("/chat/", json={
            "content": "Xin chào, tôi cảm thấy hơi lo lắng về công việc."
        })
        
        runner.assert_status_code("Send Message - Status 200", response, 200)
        
        if response.status_code == 200:
            data = response.json()
            runner.assert_has_key("Chat - Has content", data, "content")
            runner.assert_has_key("Chat - Has role", data, "role")
            runner.assert_equal("Chat - Role is assistant", data.get("role"), "assistant")
            runner.assert_true("Chat - Content not empty", len(data.get("content", "")) > 0)
            
            # Check for sources
            if "sources" in data:
                print(f"    RAG Sources: {len(data['sources'])} found")
    
    # ===== Test 3: Get Chat History =====
    print_section("Test 3: Get Chat History")
    
    if not client.conversation_id:
        print("    ⚠️  Skipping - No conversation ID")
    else:
        response = client.get(f"/chat/history/?conversation_id={client.conversation_id}")
        
        runner.assert_status_code("History - Status 200", response, 200)
        
        if response.status_code == 200:
            data = response.json()
            runner.assert_has_key("History - Has messages", data, "messages")
            
            messages = data.get("messages", [])
            runner.assert_true("History - Has messages", len(messages) >= 2)  # User + Assistant
            
            if len(messages) >= 2:
                print(f"    Messages found: {len(messages)}")
                # Verify message structure
                first_msg = messages[0]
                runner.assert_has_key("Message - Has role", first_msg, "role")
                runner.assert_has_key("Message - Has content", first_msg, "content")
    
    # ===== Test 4: Empty Message Validation =====
    print_section("Test 4: Validation - Empty Message")
    
    if not client.session_id:
        print("    ⚠️  Skipping - No session ID")
    else:
        response = client.post("/chat/", json={
            "content": ""
        })
        
        runner.assert_status_code("Empty Message - Status 422", response, 422)
    
    # ===== Test 5: Session Info =====
    print_section("Test 5: Get Session Info")
    
    if not client.session_id:
        print("    ⚠️  Skipping - No session ID")
    else:
        response = client.get("/sessions/info/")
        
        runner.assert_status_code("Session Info - Status 200", response, 200)
        
        if response.status_code == 200:
            data = response.json()
            runner.assert_has_key("Info - Has session_id", data, "session_id")
            runner.assert_equal("Info - Session ID matches", 
                              data.get("session_id"), client.session_id)
    
    # Print summary
    success = runner.finish()
    return success


if __name__ == "__main__":
    try:
        success = test_chat_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
