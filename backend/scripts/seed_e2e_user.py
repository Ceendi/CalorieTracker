"""
Seed script for E2E test users.

Creates/resets 3 test users for Maestro E2E tests:
1. Fully onboarded user (e2e-test@calorietracker.dev)
2. Cleans up registration target (e2e-register@calorietracker.dev)
3. Verified but not onboarded user (e2e-onboard@calorietracker.dev)

Usage:
    cd backend
    uv run python scripts/seed_e2e_user.py
"""

import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi_users.password import PasswordHelper

from src.core.config import settings
from src.users.domain.models import User


password_helper = PasswordHelper()

E2E_PASSWORD = "TestPass123!"
HASHED_PASSWORD = password_helper.hash(E2E_PASSWORD)

USERS = [
    {
        "email": "e2e-test@calorietracker.dev",
        "hashed_password": HASHED_PASSWORD,
        "is_active": True,
        "is_verified": True,
        "is_superuser": False,
        "is_onboarded": True,
        "age": 25,
        "gender": "male",
        "height": 180.0,
        "weight": 75.0,
        "goal": "maintain",
        "activity_level": "moderate",
    },
    {
        "email": "e2e-onboard@calorietracker.dev",
        "hashed_password": HASHED_PASSWORD,
        "is_active": True,
        "is_verified": True,
        "is_superuser": False,
        "is_onboarded": False,
        "age": None,
        "gender": None,
        "height": None,
        "weight": None,
        "goal": None,
        "activity_level": None,
    },
]


async def seed():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        # 1. Delete registration target so the registration test can create it fresh
        registration_email = "e2e-register@calorietracker.dev"
        result = await session.execute(
            select(User).where(User.email == registration_email)
        )
        existing = result.unique().scalar_one_or_none()
        if existing:
            await session.delete(existing)
            print(f"  Deleted existing: {registration_email}")
        else:
            print(f"  Clean (no existing): {registration_email}")

        # 2. Upsert the seeded users
        for user_data in USERS:
            email = user_data["email"]
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.unique().scalar_one_or_none()

            if existing_user:
                # Update existing user to reset state
                for key, value in user_data.items():
                    if key != "email":
                        setattr(existing_user, key, value)
                print(f"  Updated: {email}")
            else:
                # Create new user
                new_user = User(id=uuid.uuid4(), **user_data)
                session.add(new_user)
                print(f"  Created: {email}")

        await session.commit()

    await engine.dispose()
    print("\nE2E seed complete.")


if __name__ == "__main__":
    print("Seeding E2E test users...")
    asyncio.run(seed())
