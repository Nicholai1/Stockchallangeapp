from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models
from app.schemas import user as user_schema
from app.database import get_db
from app.utils import auth

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/", response_model=user_schema.UserRead)
def create_user(user_in: user_schema.UserCreate, db: Session = Depends(get_db)):
    """
    Opret en ny bruger.
    - Tjekker om brugernavn allerede eksisterer
    - Hasher password
    - Gemmer i databasen
    - Returnerer brugerdata
    """
    # Tjek om brugernavn allerede findes
    existing_user = db.query(models.User).filter(models.User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Brugernavn allerede taget")

    # Hash password
    hashed_pw = auth.get_password_hash(user_in.password)

    # Opret bruger
    new_user = models.User(
        username=user_in.username,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user