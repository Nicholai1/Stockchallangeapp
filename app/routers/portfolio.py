from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import UserPortfolio, StockPrice
from app.schemas.portfolio import PortfolioItem

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/{user_id}", response_model=List[PortfolioItem])
def get_portfolio(user_id: int, db: Session = Depends(get_db)):
    rows = db.query(UserPortfolio).filter(UserPortfolio.user_id == user_id).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Portefølje ikke fundet")

    items = []
    for r in rows:
        # augment with StockPrice metadata if available
        sp = db.query(StockPrice).filter(StockPrice.symbol == r.symbol).first()
        item = PortfolioItem.model_validate(r)
        # model_validate returns a pydantic model; convert to dict then set extra fields
        d = item.model_dump()
        d['name'] = sp.name if sp and sp.name else d.get('name')
        d['currency'] = sp.currency if sp and sp.currency else d.get('currency')
        items.append(d)

    return items
