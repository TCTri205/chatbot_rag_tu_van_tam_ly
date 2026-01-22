"""
Script to create an admin user for the chatbot system.
This script creates a new admin user or promotes an existing user to admin.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.user import User, UserRole
from src.core.security import hash_password
from src.core.config import settings


async def create_admin_user(
    username: str,
    email: str,
    password: str,
    role: str = "admin"
):
    """
    Create a new admin user or promote existing user to admin.
    
    Args:
        username: Username for the admin
        email: Email address
        password: Password (will be hashed)
        role: Either 'admin' or 'super_admin' (default: 'admin')
    """
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Check if user already exists by email
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠️  User with email '{email}' already exists!")
                print(f"   Current role: {existing_user.role}")
                print(f"   Username: {existing_user.username}")
                
                # Ask if user wants to promote
                if existing_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                    print(f"✅ User is already an admin!")
                    return
                
                response = input(f"\nPromote this user to {role}? (yes/no): ").strip().lower()
                if response == 'yes':
                    # Update role
                    existing_user.role = UserRole.ADMIN if role == "admin" else UserRole.SUPER_ADMIN
                    existing_user.is_active = True
                    await session.commit()
                    print(f"✅ User '{email}' promoted to {role} successfully!")
                else:
                    print("❌ Operation cancelled.")
                return
            
            # Create new admin user
            hashed_password = hash_password(password)
            
            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_password,
                role=UserRole.ADMIN if role == "admin" else UserRole.SUPER_ADMIN,
                is_active=True
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            print(f"\n✅ Admin user created successfully!")
            print(f"   User ID: {new_user.id}")
            print(f"   Username: {new_user.username}")
            print(f"   Email: {new_user.email}")
            print(f"   Role: {new_user.role}")
            print(f"\n🔑 You can now login with:")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()


async def interactive_create_admin():
    """Interactive mode to create admin user."""
    print("=" * 60)
    print("        Tạo Tài Khoản Admin - TamLy Bot")
    print("=" * 60)
    print()
    
    # Get user input
    username = input("Tên người dùng (username): ").strip()
    if not username:
        print("❌ Username không được để trống!")
        return
    
    email = input("Email: ").strip()
    if not email or "@" not in email:
        print("❌ Email không hợp lệ!")
        return
    
    password = input("Mật khẩu (tối thiểu 8 ký tự): ").strip()
    if len(password) < 8:
        print("❌ Mật khẩu phải có ít nhất 8 ký tự!")
        return
    
    confirm_password = input("Xác nhận mật khẩu: ").strip()
    if password != confirm_password:
        print("❌ Mật khẩu xác nhận không khớp!")
        return
    
    print("\nChọn vai trò:")
    print("  1. admin - Quản trị viên thông thường")
    print("  2. super_admin - Quản trị viên cấp cao")
    role_choice = input("Chọn (1/2) [mặc định: 1]: ").strip() or "1"
    
    role = "admin" if role_choice == "1" else "super_admin"
    
    print(f"\n📋 Thông tin tài khoản:")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Role: {role}")
    
    confirm = input("\nXác nhận tạo tài khoản? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ Hủy tạo tài khoản.")
        return
    
    print("\n🔄 Đang tạo tài khoản...")
    await create_admin_user(username, email, password, role)


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Command line mode
        if len(sys.argv) != 4:
            print("Usage: python create_admin.py <username> <email> <password>")
            print("   Or: python create_admin.py (for interactive mode)")
            sys.exit(1)
        
        username = sys.argv[1]
        email = sys.argv[2]
        password = sys.argv[3]
        
        await create_admin_user(username, email, password)
    else:
        # Interactive mode
        await interactive_create_admin()


if __name__ == "__main__":
    asyncio.run(main())
