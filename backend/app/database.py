import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

is_testing = os.environ.get("TESTING") == "1"
db_url = "sqlite:///./docmind_test.db" if is_testing else settings.DATABASE_URL

# Normalize older PostgreSQL URL format.
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

def validate_database_url(url: str, environment: str) -> str:
    """
    Validates that production environments strictly use PostgreSQL.
    Raises RuntimeError if SQLite or non-PostgreSQL backend is configured in production.
    Returns normalized database backend name.
    """
    normalized_url = url.replace("postgres://", "postgresql://", 1) if url.startswith("postgres://") else url
    parsed = make_url(normalized_url)
    backend_name = parsed.get_backend_name()
    is_prod = environment.strip().lower() == "production"

    if is_prod and backend_name != "postgresql":
        raise RuntimeError(
            "Production requires a PostgreSQL DATABASE_URL. "
            "SQLite is permitted only in development."
        )
    return backend_name


# Parse and validate the configured database safely.
database_backend = validate_database_url(db_url, settings.ENVIRONMENT)

# Apply connection arguments appropriate to each database.
connect_args = {}

if database_backend == "sqlite":
    connect_args["check_same_thread"] = False
elif database_backend == "postgresql":
    connect_args["connect_timeout"] = 5

try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )

    # Verify connectivity during application startup.
    with engine.connect():
        pass

    logger.info(
        "Database connection established. Backend: %s",
        database_backend,
    )

except Exception as e:
    # Do not log the database URL: it may contain credentials.
    logger.error(
        "Failed to connect to configured database. Error type: %s",
        type(e).__name__,
    )
    raise

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, always closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
