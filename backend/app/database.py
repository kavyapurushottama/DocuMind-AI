import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

def _init_engine(url: str):
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)

try:
    engine = _init_engine(db_url)
    with engine.connect() as conn:
        pass
except Exception as e:
    if not db_url.startswith("sqlite"):
        logger.warning(f"Failed to connect to PostgreSQL ({e}). Falling back to local SQLite (sqlite:///./docmind.db)...")
        db_url = "sqlite:///./docmind.db"
        engine = _init_engine(db_url)
    else:
        raise e

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, always closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
