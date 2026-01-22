import asyncio
from sqlalchemy import select
from src.models.user import User
from src.database import async_session_maker
from src.core.security import verify_password

async def check_users():
    async with async_session_maker() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print("=" * 50)
        print("ALL USERS IN DATABASE")
        print("=" * 50)
        
        for user in users:
            print(f"\n📧 Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Role: {user.role}")
            print(f"   Active: {user.is_active}")
            print(f"   Anonymous: {user.is_anonymous}")
            
        print("\n" + "=" * 50)
        print("TESTING PASSWORD VERIFICATION")
        print("=" * 50)
        
        # Test admin@example.com
        result = await session.execute(select(User).where(User.email == 'admin@example.com'))
        admin_user = result.scalar_one_or_none()
        
        if admin_user:
            test_password = 'abcd1234'
            is_valid = verify_password(test_password, admin_user.password_hash)
            print(f"\n✅ User 'admin@example.com' found")
            print(f"   Password 'abcd1234' valid: {is_valid}")
        else:
            print(f"\n❌ User 'admin@example.com' NOT found")
            
        # Test admin@gmail.com
        result = await session.execute(select(User).where(User.email == 'admin@gmail.com'))
        gmail_user = result.scalar_one_or_none()
        
        if gmail_user:
            print(f"\n✅ User 'admin@gmail.com' found")
            print(f"   Role: {gmail_user.role}")
        else:
            print(f"\n❌ User 'admin@gmail.com' NOT found")

asyncio.run(check_users())
