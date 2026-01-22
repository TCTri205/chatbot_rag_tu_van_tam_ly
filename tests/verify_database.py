"""
Database Integrity Verification Script
Checks database state after tests to ensure data consistency
"""
import psycopg2
from datetime import datetime, timedelta
import json

import psycopg2
from datetime import datetime, timedelta
import json
import os

# Database connection settings
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "chatbot_db"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "password")
}

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"💡 If using Docker, use port from docker-compose or exec into container")
        return None

def verify_database_integrity():
    """Run all database integrity checks"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    all_checks_passed = True
    
    print("\n" + "="*60)
    print("DATABASE INTEGRITY VERIFICATION")
    print("="*60 + "\n")
    
    # Check 1: Orphaned messages
    print("📋 Check 1: Orphaned Messages")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM messages m 
        LEFT JOIN conversations c ON m.conversation_id = c.id 
        WHERE c.id IS NULL
    """)
    orphaned_count = cursor.fetchone()[0]
    if orphaned_count == 0:
        print(f"✅ No orphaned messages found")
    else:
        print(f"❌ Found {orphaned_count} orphaned messages")
        all_checks_passed = False
    
    # Check 2: User conversations
    print("\n📋 Check 2: User Conversation Counts")
    cursor.execute("""
        SELECT u.username, u.email, COUNT(c.id) as conversation_count
        FROM users u
        LEFT JOIN conversations c ON u.id = c.user_id
        WHERE u.is_anonymous = false
        GROUP BY u.id, u.username, u.email
        ORDER BY conversation_count DESC
        LIMIT 5
    """)
    print("Top 5 users by conversation count:")
    for row in cursor.fetchall():
        print(f"  - {row[0]} ({row[1]}): {row[2]} conversations")
    print("✅ User conversation check complete")
    
    # Check 3: Audit logs for recent actions
    print("\n📋 Check 3: Recent Audit  Logs (Last 24h)")
    cursor.execute("""
        SELECT action, COUNT(*) as count
        FROM audit_logs 
        WHERE created_at > NOW() - INTERVAL '1 day'
        GROUP BY action
        ORDER BY count DESC
    """)
    audit_entries = cursor.fetchall()
    if audit_entries:
        print("Recent audit actions:")
        for action, count in audit_entries:
            print(f"  - {action}: {count} times")
    else:
        print("  No audit logs in last 24 hours")
    print("✅ Audit log check complete")
    
    # Check 4: Metadata column exists
    print("\n📋 Check 4: Audit Logs Metadata Column (Sprint 4)")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'audit_logs' 
          AND column_name = 'metadata'
    """)
    metadata_column = cursor.fetchone()
    if metadata_column:
        print(f"✅ Metadata column exists: {metadata_column[1]} (nullable: {metadata_column[2]})")
    else:
        print(f"❌ Metadata column NOT FOUND")
        all_checks_passed = False
    
    # Check 5: SOS/Crisis messages
    print("\n📋 Check 5: Crisis Messages (SOS Flagged)")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM messages 
        WHERE is_sos = true
    """)
    sos_count = cursor.fetchone()[0]
    print(f"✅ Total SOS messages flagged: {sos_count}")
    
    # Check 6: Mood entries
    print("\n📋 Check 6: Mood Entries")
    cursor.execute("""
        SELECT mood_label, COUNT(*) as count
        FROM mood_entries
        GROUP BY mood_label
        ORDER BY count DESC
    """)
    mood_stats = cursor.fetchall()
    if mood_stats:
        print("Mood distribution:")
        for label, count in mood_stats:
            print(f"  - {label}: {count} entries")
    else:
        print("  No mood entries found")
    print("✅ Mood entry check complete")
    
    # Check 7: Feedback entries
    print("\n📋 Check 7: Feedback Entries")
    cursor.execute("""
        SELECT 
            CASE WHEN rating > 0 THEN 'Positive' ELSE 'Negative' END as feedback_type,
            COUNT(*) as count
        FROM feedbacks
        GROUP BY CASE WHEN rating > 0 THEN 'Positive' ELSE 'Negative' END
    """)
    feedback_stats = cursor.fetchall()
    if feedback_stats:
        print("Feedback distribution:")
        for fb_type, count in feedback_stats:
            print(f"  - {fb_type}: {count} feedbacks")
    else:
        print("  No feedback entries found")
    print("✅ Feedback check complete")
    
    # Check 8: Active vs Banned users
    print("\n📋 Check 8: User Status Distribution")
    cursor.execute("""
        SELECT 
            is_active,
            role,
            COUNT(*) as count
        FROM users
        WHERE is_anonymous = false
        GROUP BY is_active, role
        ORDER BY role, is_active DESC
    """)
    user_stats = cursor.fetchall()
    print("User status by role:")
    for is_active, role, count in user_stats:
        status = "Active" if is_active else "Banned"
        print(f"  - {role} ({status}): {count} users")
    print("✅ User status check complete")
    
   # Check 9: Recent conversations
    print("\n📋 Check 9: Recent Activity (Last 7 days)")
    cursor.execute("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as conversation_count
        FROM conversations
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """)
    recent_activity = cursor.fetchall()
    if recent_activity:
        print("Daily conversation creation:")
        for date, count in recent_activity:
            print(f"  - {date}: {count} conversations")
    else:
        print("  No conversations in last 7 days")
    print("✅ Activity check complete")
    
    # Check 10: System settings
    print("\n📋 Check 10: System Settings")
    cursor.execute("""
        SELECT key, LEFT(value, 50) as value_preview, updated_at
        FROM system_settings
        ORDER BY key
    """)
    settings = cursor.fetchall()
    if settings:
        print("Current system settings:")
        for key, value, updated in settings:
            print(f"  - {key}: {value}... (updated: {updated})")
    else:
        print("  No system settings found")
    print("✅ System settings check complete")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    if all_checks_passed:
        print("✅ ALL DATABASE INTEGRITY CHECKS PASSED")
    else:
        print("❌ SOME CHECKS FAILED - Review above")
    print("="*60 + "\n")
    
    return all_checks_passed

def verify_test_user_data(test_email):
    """Verify specific test user's data"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    print(f"\n🔍 Verifying test user: {test_email}")
    
    # Get user
    cursor.execute("SELECT id, username, role, is_active FROM users WHERE email = %s", (test_email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User not found: {test_email}")
        cursor.close()
        conn.close()
        return
    
    user_id, username, role, is_active = user
    print(f"✅ User found: {username} (Role: {role}, Active: {is_active})")
    
    # Check conversations
    cursor.execute("""
        SELECT COUNT(*), MAX(created_at)
        FROM conversations
        WHERE user_id = %s
    """, (user_id,))
    conv_count, last_conv = cursor.fetchone()
    print(f"  Conversations: {conv_count} (Last: {last_conv})")
    
    # Check messages
    cursor.execute("""
        SELECT COUNT(*)
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.user_id = %s
    """, (user_id,))
    msg_count = cursor.fetchone()[0]
    print(f"  Messages: {msg_count}")
    
    # Check mood entries
    cursor.execute("""
        SELECT COUNT(*)
        FROM mood_entries
        WHERE user_id = %s
    """, (user_id,))
    mood_count = cursor.fetchone()[0]
    print(f"  Mood entries: {mood_count}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("\n🔧 Starting Database Verification...")
    print("Note: This script connects to PostgreSQL on localhost:5432")
    print("If using Docker, you may need to:")
    print("  1. Expose port 5432 in docker-compose.yml, OR")
    print("  2. Run this script inside the container")
    print()
    
    success = verify_database_integrity()
    
    # Optionally verify specific test user
    # verify_test_user_data("test@example.com")
    
    exit(0 if success else 1)
