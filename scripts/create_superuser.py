#!/usr/bin/env python3
"""
Create a superuser interactively.

Usage:
    python scripts/create_superuser.py
"""
import asyncio
import getpass
import sys
import os

# Make sure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User


async def main() -> None:
    print("=== Create superuser ===")
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match.", file=sys.stderr)
        sys.exit(1)
    if not username or not email or not password:
        print("All fields are required.", file=sys.stderr)
        sys.exit(1)

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
        if existing:
            print(f"User '{username}' already exists.", file=sys.stderr)
            sys.exit(1)

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        await db.commit()
        print(f"Superuser '{username}' created successfully.")


if __name__ == "__main__":
    asyncio.run(main())
