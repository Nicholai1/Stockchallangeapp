from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserRead
from pydantic import BaseModel
from app import models
from app.utils.auth import verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=UserRead)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user
