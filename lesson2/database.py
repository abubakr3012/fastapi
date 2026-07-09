from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/books"

engine = create_async_engine(
    DATABASE_URL,
    echo=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


class Base(DeclarativeBase):
    pass