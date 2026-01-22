import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.models.user import User, UserRole
from src.core.security import get_password_hash
from src.config import settings

# Hardcoded credentials for quick creation
USERNAME = "admin"
EMAIL = "admin@gmail.com"
PASSWORD = "password123"
ROLE = UserRole.ADMIN

async def create_admin():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == EMAIL))
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f'User {EMAIL} already exists.')
            if existing.role != ROLE:
                existing.role = ROLE
                existing.is_active = True
                await session.commit()
                print(f'✅ Promoted {EMAIL} to {ROLE}!')
            else:
                # Ensure password is updated if they forgot it? 
                # Be careful not to overwrite if not intended. 
                # But for "I want to create", maybe resetting is good?
                # Let's just create if not exists or promote.
                print(f'✅ User {EMAIL} is already {ROLE}.')
        else:
            hashed = get_password_hash(PASSWORD)
            user = User(
                username=USERNAME,
                email=EMAIL,
                password_hash=hashed,
                role=ROLE,
                is_active=True
            )
            session.add(user)
            await session.commit()
            print(f'✅ Created admin user: {USERNAME} ({EMAIL})')
            print(f'   Password: {PASSWORD}')

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_admin())
