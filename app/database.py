from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ------------------------------------------------------------
# 1. Database URL
# ------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./portfolio.db"
# (Skift evt. til PostgreSQL senere)
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@host:port/dbname"

# ------------------------------------------------------------
# 2. Engine
# ------------------------------------------------------------
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Kun nødvendigt for SQLite
)

# ------------------------------------------------------------
# 3. Session & Base
# ------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base metadata
Base = declarative_base()


# ------------------------------------------------------------
# 4. Dependency til FastAPI
# ------------------------------------------------------------
def get_db():
    """Returnér en ny database-session til hver request"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
