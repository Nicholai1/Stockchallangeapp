from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Database URL hentes fra config
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Opret SQLAlchemy engine (SQLite til udvikling)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal bruges i endpoints til at få DB-sessioner
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base er "grundklassen" som alle modeller arver fra
Base = declarative_base()


# Dependency som bruges i endpoints:
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()