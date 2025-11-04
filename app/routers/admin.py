from fastapi import APIRouter, HTTPException, Depends, Header
import os
from typing import Optional
from app.database import SessionLocal
from app.services.price_updater import recompute_portfolios_for_symbol

router = APIRouter(prefix="/admin")


def _check_token(x_admin_token: Optional[str] = Header(None)):
    expected = os.environ.get('ADMIN_TOKEN')
    if expected and x_admin_token == expected:
        return True
    if expected is None:
        # no token configured -> deny to be safe
        raise HTTPException(status_code=403, detail='Admin token not configured')
    raise HTTPException(status_code=401, detail='Invalid admin token')


@router.post('/recompute')
def recompute(symbol: Optional[str] = None, ok: bool = Depends(_check_token)):
    """Trigger recompute for a single symbol or for all symbols if none provided.

    Protected by ADMIN_TOKEN environment variable; pass header 'x-admin-token: <token>'.
    """
    db = SessionLocal()
    try:
        if symbol:
            recompute_portfolios_for_symbol(db, symbol)
            db.commit()
            return { 'ok': True, 'symbol': symbol }
        # recompute for all tracked symbols
        from app.models import StockPrice
        syms = [s.symbol for s in db.query(StockPrice).all()]
        for s in syms:
            recompute_portfolios_for_symbol(db, s)
        db.commit()
        return { 'ok': True, 'symbols': syms }
    finally:
        db.close()
