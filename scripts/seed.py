"""
SED Energy AI Marketing System — Database Seed Script
Run via: make seed
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from app.config import get_settings
from app.models.user import User
from app.models.social import SocialAccount

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create default super admin
        admin = User(
            email="admin@sed.energy",
            hashed_password=pwd_context.hash("SED@dmin2024\!"),
            full_name="SED Admin",
            role="super_admin",
            is_active=True,
        )
        session.add(admin)

        # Create marketing manager
        manager = User(
            email="marketing@sed.energy",
            hashed_password=pwd_context.hash("Marketing2024\!"),
            full_name="Marketing Manager",
            role="marketing_manager",
            is_active=True,
        )
        session.add(manager)

        # Create social accounts
        platforms = [
            {"platform": "facebook", "account_name": "SED Energy SA", "account_id": ""},
            {"platform": "instagram", "account_name": "@sed_energy_sa", "account_id": ""},
            {"platform": "linkedin", "account_name": "SED Energy", "account_id": ""},
            {"platform": "whatsapp", "account_name": "SED WhatsApp Business", "account_id": ""},
        ]
        for p in platforms:
            session.add(SocialAccount(**p))

        await session.commit()
        print("✅ Seed complete\!")
        print("   Admin:   admin@sed.energy / SED@dmin2024\!")
        print("   Manager: marketing@sed.energy / Marketing2024\!")
        print("   ⚠️  Change these passwords immediately\!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
