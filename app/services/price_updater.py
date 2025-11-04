import concurrent.futures
import logging
import threading
import time
from datetime import datetime
from sqlalchemy import func
from typing import List
from sqlalchemy import case

from app.database import SessionLocal
from app.models import StockPrice, UserPortfolio, Transaction
from app.services.stocks import get_stock_info
from app.services import ws_manager


def recompute_portfolios_for_symbol(db, sym: str) -> None:
    """Recompute UserPortfolio rows for a single symbol using BUY transactions.

    This function expects an open SQLAlchemy session (`db`) and will upsert
    UserPortfolio rows for every user who has BUY transactions for `sym`.
    """
    try:
        # Compute buys and sells aggregates per user so we can derive net quantity and cost basis.
        portfolio_rows = (
            db.query(
                Transaction.user_id,
                func.coalesce(func.sum(case((Transaction.type.ilike('BUY'), Transaction.quantity), else_=0)), 0).label('qty_buy'),
                func.coalesce(func.sum(case((Transaction.type.ilike('SELL'), Transaction.quantity), else_=0)), 0).label('qty_sell'),
                func.coalesce(func.sum(case((Transaction.type.ilike('BUY'), Transaction.total_amount), else_=0)), 0).label('spent_buy'),
                func.coalesce(func.sum(case((Transaction.type.ilike('SELL'), Transaction.total_amount), else_=0)), 0).label('received_sell')
            )
            .filter(Transaction.symbol == sym)
            .group_by(Transaction.user_id)
            .all()
        )

        processed_user_ids = set()

        for pr in portfolio_rows:
            user_id = pr[0]
            qty_buy = pr[1] or 0
            qty_sell = pr[2] or 0
            spent_buy = pr[3] or 0
            received_sell = pr[4] or 0

            net_qty = qty_buy - qty_sell
            net_total = spent_buy - received_sell

            # If net_qty <= 0, remove any existing portfolio row for this user/symbol
            existing = db.query(UserPortfolio).filter(
                UserPortfolio.user_id == user_id,
                UserPortfolio.symbol == sym
            ).first()

            if net_qty <= 0:
                if existing:
                    db.delete(existing)
                # nothing more to do for this user
                continue

            # compute current price and derived fields
            sp = db.query(StockPrice).filter(StockPrice.symbol == sym).first()
            current_price = sp.current_price if sp else 0
            current_amount = net_qty * current_price
            avg_cost = (net_total / net_qty) if net_qty > 0 else 0.0
            profit = current_amount - net_total

            processed_user_ids.add(user_id)

            if existing:
                existing.quantity = net_qty
                existing.total_amount = net_total
                existing.avg_cost = avg_cost
                existing.current_amount = current_amount
                existing.profit = profit
                db.add(existing)
            else:
                up = UserPortfolio(
                    user_id=user_id,
                    symbol=sym,
                    quantity=net_qty,
                    total_amount=net_total,
                    avg_cost=avg_cost,
                    current_amount=current_amount,
                    profit=profit,
                )
                db.add(up)

        # Remove any UserPortfolio rows for this symbol that weren't in the processed_user_ids
        if processed_user_ids:
            db.query(UserPortfolio).filter(UserPortfolio.symbol == sym, ~UserPortfolio.user_id.in_(list(processed_user_ids))).delete(synchronize_session=False)
        else:
            # no users have positions for this symbol: remove all portfolio rows for the symbol
            db.query(UserPortfolio).filter(UserPortfolio.symbol == sym).delete(synchronize_session=False)
    except Exception:
        _logger.exception("Error recomputing portfolios for %s", sym)

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
                        # If the fetch returned an explicit error indicating symbol not found,
                        # remove the StockPrice row to avoid keeping invalid symbols in the registry.
                        err = info.get('error') if isinstance(info, dict) else None
                        if err and ('Quote not found' in err or 'Not Found' in err or '404' in err or 'Quote not found for symbol' in err):
                            try:
                                db.delete(sp)
                            except Exception:
                                _logger.exception("Failed to delete invalid StockPrice %s", sym)
                            continue

                        sp.current_price = info.get("price", sp.current_price)
                        sp.name = info.get("name", sp.name)
                        sp.currency = info.get("currency", sp.currency)
                        db.add(sp)

                    # enqueue websocket messages for live updates
                    try:
                        for sym, info in results:
                            msg = {
                                'type': 'price_update',
                                'symbol': sym,
                                'price': info.get('price'),
                                'name': info.get('name'),
                                'currency': info.get('currency'),
                                'last_updated': info.get('last_updated')
                            }
                            # non-async thread -> enqueue safely
                            ws_manager.enqueue_message_from_thread(msg)
                    except Exception:
                        _logger.exception("Failed to enqueue websocket messages")

                    db.commit()
                    # After updating prices, recompute user portfolios for affected symbols
                    try:
                        # Recompute portfolios for symbols we just updated
                        for sym, info in results:
                            recompute_portfolios_for_symbol(db, sym)
                        db.commit()
                    except Exception:
                        _logger.exception("Failed to recompute portfolios")
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
