from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"ssl": True}
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)