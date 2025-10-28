# app/utils/test_create_user.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.routers import user as user_router
from app.schemas import user as user_schema
from app import models
from app.utils import auth

# Lav en midlertidig SQLite database i hukommelsen
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Opret tabeller
Base.metadata.create_all(bind=engine)

# Funktion til at få en test-session
def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_create_user(username: str, password: str):
    # Hent test-session
    db_gen = get_test_db()
    db = next(db_gen)

    # Tjek om brugernavn allerede findes
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        print(f"Brugernavn '{username}' findes allerede!")
        return

    # Hash password
    hashed_pw = auth.get_password_hash(password)

    # Opret bruger
    new_user = models.User(username=username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(f"Bruger oprettet: ID={new_user.id}, Username={new_user.username}, Created_at={new_user.created_at}")

# Eksempel test
if __name__ == "__main__":
    test_create_user("testuser1", "Hemmelig123")
    test_create_user("testuser2", "123456")
    test_create_user("testuser1", "Hemmelig123")