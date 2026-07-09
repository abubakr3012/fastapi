from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
DATABASE_URL='postgresql:asyncpg://postgres:1234@localhost:5432/book_db'

engine=create_async_engine(
    DATABASE_URL,
    ech0=True
)

AsyncSessionLocal=async_sessionmaker(
    engine
)

async def get_db():
    async with AsyncSessionLocal as session:
        yield session

class Base(DeclarativeBase):
    pass

