import os
from sqlalchemy import create_engine, NullPool
from sqlalchemy.orm import sessionmaker

from app.models import Base

DB_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER', 'priceapi').strip()}:"
    f"{os.getenv('DB_PASS', 'priceapi').strip()}@{os.getenv('DB_HOST', 'localhost').strip()}:"
    f"{os.getenv('DB_PORT', '5433').strip()}/{os.getenv('DB_NAME', 'priceapi').strip()}"
)

engine=create_engine(DB_URL,poolclass=NullPool,future=True)
Sessionlocal=sessionmaker(bind=engine,autocommit=False,autoflush=False)

def init_db():
    Base.metadata.create_all(bind=engine)
def get_session():
    db=Sessionlocal()
    try:
        yield db
    finally:
        db.close()

