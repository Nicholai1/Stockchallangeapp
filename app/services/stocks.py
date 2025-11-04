import logging
import threading
import time
from typing import Optional

import yfinance as yf

_logger = logging.getLogger(__name__)

# Simple in-memory TTL cache to avoid duplicate yfinance calls in short succession.
_stock_info_cache: dict[str, tuple[float, dict]] = {}
_stock_info_lock = threading.Lock()
# Cache TTL in seconds (small to stay fresh)
_CACHE_TTL = 30


def _get_from_cache(symbol: str) -> Optional[dict]:
    now = time.time()
    with _stock_info_lock:
        entry = _stock_info_cache.get(symbol.upper())
        if entry:
            ts, data = entry
            if now - ts < _CACHE_TTL:
                return data
            # expired
            del _stock_info_cache[symbol.upper()]
    return None


def _set_cache(symbol: str, data: dict) -> None:
    with _stock_info_lock:
        _stock_info_cache[symbol.upper()] = (time.time(), data)


def get_stock_info(symbol: str, use_cache: bool = True) -> dict:
    """Return basic stock info for a ticker symbol using yfinance.

    Returns dict with keys: symbol, name, price, currency
    Set use_cache=False to force a fresh network call.
    """
    sym = symbol.upper()
    if use_cache:
        cached = _get_from_cache(sym)
        if cached is not None:
            return cached

    try:
        ticker = yf.Ticker(sym)
        # Try fast_info first
        price = None
        try:
            fast = ticker.fast_info
            price = fast.get("last_price")
        except Exception:
            price = None

        # Fallback to last close
        if not price:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist["Close"].iloc[-1]

        price = round(price, 2) if price else 0

        info = ticker.info if hasattr(ticker, "info") else {}

        result = {
            "symbol": sym,
            "name": info.get("shortName", sym),
            "price": price,
            "currency": info.get("currency", "N/A"),
        }

        # cache the result
        try:
            _set_cache(sym, result)
        except Exception:
            # cache failure shouldn't break the call
            _logger.debug("Failed to set cache for %s", sym, exc_info=True)

        return result
    except Exception as e:
        _logger.exception("Error fetching %s", sym)
        # Return an error field so callers can act (for example remove invalid symbols)
        return {"symbol": sym, "name": sym, "price": 0, "currency": "N/A", "error": str(e)}


def ensure_stock_in_db(db, symbol: str):
    """Ensure a StockPrice row exists for `symbol`. If missing, insert it with current price.

    Returns the StockPrice instance.
    """
    from app.models import StockPrice

    existing = db.query(StockPrice).filter(StockPrice.symbol == symbol).first()
    info = get_stock_info(symbol)
    if existing:
        # update metadata/price immediately
        existing.name = info.get("name", existing.name)
        existing.currency = info.get("currency", existing.currency)
        existing.current_price = info.get("price", existing.current_price)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    sp = StockPrice(
        symbol=symbol,
        name=info.get("name"),
        currency=info.get("currency"),
        current_price=info.get("price", 0),
    )
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return sp
