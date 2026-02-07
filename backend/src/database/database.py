from typing import AsyncGenerator, Annotated
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from pydantic import PostgresDsn

from core.config import settings
from database.models.base import Base
from database.models.user import User
from database.models.chat import Chat
from database.models.message import Message


class Database:
    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
    ):
        self.engine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Returns async sqlalchemy session"""
        async with self.session_factory() as session:
            yield session

    async def startup(self):
        """Start up database"""
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def dispose(self):
        """Dispose database"""
        await self.engine.dispose()


database = Database(
    url=settings.database.url,
    echo=settings.database.echo,
    echo_pool=settings.database.echo_pool,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_pre_ping=settings.database.pool_pre_ping,
)
