from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for each request and close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbDependency = Depends(get_db)
