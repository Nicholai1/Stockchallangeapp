from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import StockPrice

router = APIRouter(prefix="/stock_prices", tags=["Stocks"])


@router.get("/")
def get_stock_prices(symbols: Optional[str] = Query(None, description="Comma-separated symbols"), db: Session = Depends(get_db)):
    """Return current stock prices. If `symbols` is provided, filter by them."""
    query = db.query(StockPrice)
    if symbols:
        syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if not syms:
            raise HTTPException(status_code=400, detail="No valid symbols provided")
        query = query.filter(StockPrice.symbol.in_(syms))
    rows = query.all()
    result = []
    for r in rows:
        result.append({
            "symbol": r.symbol,
            "name": r.name,
            "currency": r.currency,
            "price": r.current_price,
            "last_updated": r.last_updated.isoformat() if r.last_updated else None,
        })
    return result


@router.get("/search")
def search_stocks(q: str = Query(..., min_length=1, description="Search term for symbol or name"), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """Search known stocks by symbol or name for frontend autocomplete.

    Returns up to `limit` matches with fields: symbol, name, price.
    """
    term = f"%{q.strip()}%"
    rows = (
        db.query(StockPrice)
        .filter(or_(StockPrice.symbol.ilike(term), StockPrice.name.ilike(term)))
        .order_by(StockPrice.symbol)
        .limit(limit)
        .all()
    )
    result = []
    for r in rows:
        result.append({
            "symbol": r.symbol,
            "name": r.name,
            "price": r.current_price,
        })
    return result
