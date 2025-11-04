#!/usr/bin/env python3
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database import SessionLocal
from app.models import Transaction, UserPortfolio

def main():
    db = SessionLocal()
    try:
        txs = db.query(Transaction).order_by(Transaction.id).all()
        print('--- Transactions ---')
        for t in txs:
            print(f'id={t.id} user={t.user_id} sym={t.symbol} type={t.type} qty={t.quantity} price={t.price} total={t.total_amount} created={t.created_at}')
        ups = db.query(UserPortfolio).order_by(UserPortfolio.id).all()
        print('\n--- UserPortfolios ---')
        for u in ups:
            print(f'id={u.id} user={u.user_id} sym={u.symbol} qty={u.quantity} total_amount={u.total_amount} avg_cost={u.avg_cost} current={u.current_amount} profit={u.profit}')
    finally:
        db.close()

if __name__ == '__main__':
    main()
