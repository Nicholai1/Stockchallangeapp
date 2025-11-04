#!/usr/bin/env python3
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database import SessionLocal
from app.models import UserPortfolio
from app.services.price_updater import recompute_portfolios_for_symbol


def main():
    db = SessionLocal()
    try:
        symbols = [r.symbol for r in db.query(UserPortfolio.symbol).distinct()]
        print('Recomputing for symbols:', symbols)
        for s in symbols:
            print('recompute', s)
            recompute_portfolios_for_symbol(db, s)
            db.commit()
        # print portfolios after
        rows = db.query(UserPortfolio).order_by(UserPortfolio.id).all()
        print('\n--- UserPortfolios after recompute ---')
        for u in rows:
            print(f'id={u.id} user={u.user_id} sym={u.symbol} qty={u.quantity} total_amount={u.total_amount} avg_cost={u.avg_cost} current={u.current_amount} profit={u.profit}')
    finally:
        db.close()

if __name__ == '__main__':
    main()
