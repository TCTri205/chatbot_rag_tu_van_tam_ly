#!/bin/bash
# Script to create admin user inside Docker container

echo "=========================================="
echo "   Tạo Tài Khoản Admin - TamLy Bot"
echo "=========================================="
echo ""

# Get user input
read -p "Username: " USERNAME
read -p "Email: " EMAIL
read -s -p "Password (min 8 chars): " PASSWORD
echo ""
read -s -p "Confirm Password: " CONFIRM_PASSWORD
echo ""

if [ "$PASSWORD" != "$CONFIRM_PASSWORD" ]; then
    echo "❌ Mật khẩu không khớp!"
    exit 1
fi

echo ""
echo "Chọn vai trò:"
echo "  1. admin"
echo "  2. super_admin"
read -p "Chọn (1/2) [default: 1]: " ROLE_CHOICE

ROLE="admin"
if [ "$ROLE_CHOICE" = "2" ]; then
    ROLE="super_admin"
fi

echo ""
echo "📋 Thông tin:"
echo "   Username: $USERNAME"
echo "   Email: $EMAIL"
echo "   Role: $ROLE"
echo ""

read -p "Xác nhận? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Hủy."
    exit 0
fi

# Execute Python script in container
docker exec -i chatbot-backend python -c "
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.models.user import User, UserRole
from src.core.security import get_password_hash
from src.config import settings

async def create_admin():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == '$EMAIL'))
        existing = result.scalar_one_or_none()
        
        if existing:
            print('⚠️  User already exists:', existing.email)
            if existing.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                print('✅ Already admin!')
                return
            existing.role = UserRole('$ROLE')
            existing.is_active = True
            await session.commit()
            print('✅ Promoted to $ROLE!')
        else:
            hashed = get_password_hash('$PASSWORD')
            user = User(
                username='$USERNAME',
                email='$EMAIL',
                password_hash=hashed,
                role=UserRole('$ROLE'),
                is_active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print('✅ Admin created!')
            print('   ID:', user.id)
            print('   Username:', user.username)
            print('   Email:', user.email)
            print('   Role:', user.role)
    await engine.dispose()

asyncio.run(create_admin())
"

echo ""
echo "🎉 Hoàn tất!"
