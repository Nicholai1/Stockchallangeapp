from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import UserPortfolio
from app.schemas.portfolio import PortfolioItem

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/{user_id}", response_model=List[PortfolioItem])
def get_portfolio(user_id: int, db: Session = Depends(get_db)):
    rows = db.query(UserPortfolio).filter(UserPortfolio.user_id == user_id).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Portefølje ikke fundet")
    # Convert SQLAlchemy objects into Pydantic models to avoid response validation errors
    items = [PortfolioItem.model_validate(r) for r in rows]
    return items
