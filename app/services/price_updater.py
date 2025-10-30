import concurrent.futures
import logging
import threading
import time
from datetime import datetime
from typing import List

from app.database import SessionLocal
from app.models import StockPrice
from app.services.stocks import get_stock_info

_logger = logging.getLogger(__name__)


def _fetch_price(symbol: str) -> tuple[str, dict]:
    """Fetch stock info for a symbol; return tuple(symbol, info).

    This function is safe to run in a thread.
    """
    info = get_stock_info(symbol, use_cache=False)
    return symbol, info


def _update_loop(stop_event: threading.Event, interval: int = 300, max_workers: int = 5):
    """Background loop that updates tracked stock prices every `interval` seconds.

    Uses a small ThreadPoolExecutor to parallelize network calls while performing a single DB commit per cycle.
    """
    while not stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                # Load all tracked stocks
                rows: List[StockPrice] = db.query(StockPrice).all()

                # Filter symbols that need update (skip if updated within interval)
                now = datetime.utcnow()
                symbols_to_update = []
                for sp in rows:
                    if sp.last_updated is None:
                        symbols_to_update.append(sp.symbol)
                        continue
                    # last_updated may be timezone-aware; normalize and compute age
                    last = sp.last_updated
                    if hasattr(last, 'tzinfo') and last.tzinfo is not None:
                        last = last.replace(tzinfo=None)
                    age = now - last
                    if age.total_seconds() >= interval:
                        symbols_to_update.append(sp.symbol)

                if symbols_to_update:
                    _logger.debug("Updating prices for %d symbols", len(symbols_to_update))

                    # Fetch in parallel with limited workers
                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as exc:
                        futures = [exc.submit(_fetch_price, sym) for sym in symbols_to_update]
                        results = []
                        for fut in concurrent.futures.as_completed(futures):
                            try:
                                sym, info = fut.result()
                                results.append((sym, info))
                            except Exception:
                                _logger.exception("Error fetching price in worker")

                    # Batch update DB in single transaction
                    for sym, info in results:
                        sp = db.query(StockPrice).filter(StockPrice.symbol == sym).first()
                        if not sp:
                            continue
                        sp.current_price = info.get("price", sp.current_price)
                        sp.name = info.get("name", sp.name)
                        sp.currency = info.get("currency", sp.currency)
                        db.add(sp)

                    db.commit()
                else:
                    _logger.debug("No symbols need updating at this cycle")
            finally:
                db.close()
        except Exception:
            _logger.exception("Top-level error in price updater loop; will retry after sleep")

        # Sleep but be responsive to stop_event
        slept = 0
        while slept < interval and not stop_event.is_set():
            time.sleep(1)
            slept += 1


def start_price_updater(interval_seconds: int = 300) -> tuple[threading.Thread, threading.Event]:
    stop_event = threading.Event()
    thread = threading.Thread(target=_update_loop, args=(stop_event, interval_seconds), daemon=True)
    thread.start()
    return thread, stop_event
