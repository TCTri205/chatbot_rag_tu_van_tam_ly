"""
Script to create admin user - to be run inside Docker container
Usage: python scripts/create_admin_in_docker.py <username> <email> <password> [role]
"""
import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.models.user import User, UserRole
from src.core.security import hash_password
from src.core.config import settings


async def create_admin(username: str, email: str, password: str, role: str = "admin"):
    """Create admin user in database."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Check if user exists
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing = result.scalar_one_or_none()
            
            # Determine role enum
            role_enum = UserRole.ADMIN if role == "admin" else UserRole.SUPER_ADMIN
            
            if existing:
                print(f"⚠️  User already exists: {existing.email}")
                
                # Check if already admin
                if existing.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                    print(f"✅ User is already {existing.role}!")
                    return
                
                # Promote to admin
                print(f"Promoting to {role}...")
                existing.role = role_enum
                existing.is_active = True
                await session.commit()
                print(f"✅ User promoted to {role}!")
                
            else:
                # Create new user
                print(f"Creating new {role} user...")
                hashed_password = hash_password(password)
                
                new_user = User(
                    username=username,
                    email=email,
                    password_hash=hashed_password,
                    role=role_enum,
                    is_active=True
                )
                
                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                
                print("✅ Admin user created successfully!")
                print(f"   ID: {new_user.id}")
                print(f"   Username: {new_user.username}")
                print(f"   Email: {new_user.email}")
                print(f"   Role: {new_user.role}")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python scripts/create_admin_in_docker.py <username> <email> <password> [role]")
        print("Example: python scripts/create_admin_in_docker.py admin admin@example.com Pass123! admin")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    role = sys.argv[4] if len(sys.argv) > 4 else "admin"
    
    print("=" * 60)
    print(f"Creating {role} user: {username} ({email})")
    print("=" * 60)
    
    asyncio.run(create_admin(username, email, password, role))
