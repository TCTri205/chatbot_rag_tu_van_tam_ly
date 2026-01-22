import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.models.user import User, UserRole
from src.core.security import get_password_hash
from src.config import settings

# Default credentials
USERNAME = "admin"
EMAIL = "admin@example.com"
PASSWORD = "abcd1234"
ROLE_VALUE = "admin"

async def create_admin():
    try:
        print(f"Connecting to DB...")
        # Ensure we can connect
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == EMAIL))
            existing = result.scalar_one_or_none()
            
            target_role = UserRole(ROLE_VALUE)
            
            if existing:
                print(f'Using existing user {EMAIL}')
                if existing.role != target_role:
                    existing.role = target_role
                    await session.commit()
                    print(f'✅ Update role to {ROLE_VALUE}.')
                else:
                    print(f'✅ User role is correct.')
                
                # Check password? (Optional, skipping complexity)
            else:
                hashed = get_password_hash(PASSWORD)
                user = User(
                    username=USERNAME,
                    email=EMAIL,
                    password_hash=hashed,
                    role=target_role,
                    is_active=True
                )
                session.add(user)
                await session.commit()
                print(f'✅ Created admin user: {USERNAME}')
                print(f'   Email: {EMAIL}')
                print(f'   Password: {PASSWORD}')

        await engine.dispose()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_admin())
