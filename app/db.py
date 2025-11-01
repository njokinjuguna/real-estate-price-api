# app/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.models import Base


def _build_default_pg_url() -> str:
    """Build a Postgres URL from the existing split env vars (your current behavior)."""
    user = os.getenv("DB_USER").strip()
    pwd  = os.getenv("DB_PASS").strip()
    host = os.getenv("DB_HOST").strip()
    port = os.getenv("DB_PORT").strip()
    name = os.getenv("DB_NAME").strip()
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"


# Prefer DATABASE_URL if provided (works for SQLite or Postgres); otherwise use split vars.
DATABASE_URL = (os.getenv("DATABASE_URL") or _build_default_pg_url()).strip()

# Engine kwargs:
# - pool_pre_ping=True avoids broken-connection errors on serverless/idle resumes.
# - NullPool is a good default on ephemeral platforms (Koyeb/Render) to avoid keeping idle conns.
engine_kwargs = dict(pool_pre_ping=True, poolclass=NullPool, future=True)

# SQLite needs a tiny tweak for multithreaded FastAPI.
if DATABASE_URL.startswith("sqlite"):
    # Example: sqlite:////data/app.db
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """FastAPI dependency: provide a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
