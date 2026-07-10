"""Module de base de données."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import get_settings

Base = declarative_base()

engine = None
async_session_maker = None


async def init_db():
    """Initialise la base de données."""
    global engine, async_session_maker

    settings = get_settings()

    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")

    engine = create_async_engine(db_url, echo=settings.debug)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        from app.database.models import Base
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Retourne une session de base de données."""
    async with async_session_maker() as session:
        yield session
