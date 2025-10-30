#!/usr/bin/env python3
"""Recompute all portfolios by symbol and print summary.
Run from project root: python scripts/recompute_portfolios.py
"""
from app.database import SessionLocal
from app import models
from app.services.price_updater import recompute_portfolios_for_symbol


def main():
    s = SessionLocal()
    try:
        symbols = [sp.symbol for sp in s.query(models.StockPrice).all()]
        print('Found symbols:', symbols)
        for sym in symbols:
            print('Recomputing', sym)
            recompute_portfolios_for_symbol(s, sym)
        s.commit()

        # Print a short summary
        rows = s.query(models.UserPortfolio).all()
        print('UserPortfolio rows:', len(rows))
        for r in rows:
            print(r.user_id, r.symbol, r.quantity, r.total_amount, getattr(r, 'avg_cost', None), r.current_amount, r.profit)
    finally:
        s.close()


if __name__ == '__main__':
    main()
