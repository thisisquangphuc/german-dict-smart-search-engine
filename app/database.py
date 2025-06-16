from sqlmodel import SQLModel, create_engine, Session
import os
from pathlib import Path
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create data directory if it doesn't exist
data_dir = Path("app/data")
data_dir.mkdir(exist_ok=True)

# Database URL
DATABASE_URL = f"sqlite+aiosqlite:///{data_dir}/pons_cache.db"

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    """Initialize the database by creating all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

@asynccontextmanager
async def get_session():
    """Get an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise 