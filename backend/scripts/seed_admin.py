#!/usr/bin/env python3
"""
Create initial admin user.
Usage: python scripts/seed_admin.py
Set env vars ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME to override defaults.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal, engine, Base
from app.models.user import User, UserRole
from app.core.security import hash_password
from sqlalchemy import select
import uuid


async def seed():
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    email = os.environ.get("ADMIN_EMAIL", "admin@sed.energy")
    password = os.environ.get("ADMIN_PASSWORD", "SedAdmin2025!")
    full_name = os.environ.get("ADMIN_NAME", "SED Admin")

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"✅ Admin user {email} already exists.")
            return

        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.commit()
        print(f"✅ Admin user created: {email} / {password}")


if __name__ == "__main__":
    asyncio.run(seed())
