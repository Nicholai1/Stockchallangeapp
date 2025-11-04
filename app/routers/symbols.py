from fastapi import APIRouter, Query, Depends
from typing import List
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import StockPrice
import json
import os

router = APIRouter(prefix="/symbols", tags=["Symbols"])

# Load local symbol registry file if present
_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'symbols.json')
_local_registry = None
if os.path.exists(_REGISTRY_PATH):
    try:
        with open(_REGISTRY_PATH, 'r', encoding='utf-8') as f:
            _local_registry = json.load(f)
    except Exception:
        _local_registry = None


@router.get('/search')
def search_symbols(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)) -> List[dict]:
    term = f"%{q.strip()}%"
    results = []
    # search DB StockPrice first
    rows = db.query(StockPrice).filter(
        (StockPrice.symbol.ilike(term)) | (StockPrice.name.ilike(term))
    ).limit(limit).all()
    for r in rows:
        results.append({"symbol": r.symbol, "name": r.name or r.symbol, "price": r.current_price})

    # if we still need more, search local registry (avoid duplicates)
    if _local_registry and len(results) < limit:
        seen = {r['symbol'] for r in results}
        for item in _local_registry:
            sym = item.get('symbol')
            name = item.get('name')
            if sym in seen:
                continue
            if q.lower() in sym.lower() or (name and q.lower() in name.lower()):
                results.append({"symbol": sym, "name": name, "price": None})
                seen.add(sym)
            if len(results) >= limit:
                break

    return results
