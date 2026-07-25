import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent

# Storage directory for SQLite database
STORAGE_DIR = BACKEND_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_FILE = STORAGE_DIR / "wikimind.db"
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_FILE}"

# Retrieve DATABASE_URL from environment or fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# Configure SQLAlchemy Engine
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

# Session factory & Base model
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI Dependency for Database Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all database tables defined in models.py"""
    from BackEnd import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
