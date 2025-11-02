import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL

from app.models import Base

def _safe_int(v):
    try:
        return int(v) if v not in (None, "", "None") else None
    except Exception:
        return None

def build_database_url() -> str | URL:
    # Prefer a full DATABASE_URL if present (Koyeb/Render/Railway style)
    raw = os.getenv("DATABASE_URL", "").strip()
    if raw:
        # Normalize scheme for SQLAlchemy + psycopg2
        if raw.startswith("postgres://"):
            raw = raw.replace("postgres://", "postgresql+psycopg2://", 1)
        elif raw.startswith("postgresql://") and "postgresql+psycopg2://" not in raw:
            raw = raw.replace("postgresql://", "postgresql+psycopg2://", 1)
        return raw

    user = os.getenv("DB_USER", "priceapi").strip()
    pwd  = os.getenv("DB_PASS", "priceapi").strip()
    host = os.getenv("DB_HOST", "localhost").strip()
    db   = os.getenv("DB_NAME", "priceapi").strip()
    port = _safe_int(os.getenv("DB_PORT", "5433").strip())

    # Build via URL.create so we don't accidentally put ':None' in the string
    return URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=pwd,
        host=host,
        port=port,       # None is OK, it will omit the port
        database=db,
    )

DATABASE_URL = build_database_url()

# Engine options (no connection pool is fine for serverless; tweak as you like)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
