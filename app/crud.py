from sqlalchemy.orm import Session
from . import models, schemas
from .services.stocks import get_stock_info


def create_transaction(db: Session, user_id: int, transaction: schemas.TransactionCreate):
    # Hent aktiedata
    stock_data = get_stock_info(transaction.symbol)
    current_price = stock_data.get("price", 0)

    db_transaction = models.Transaction(
        user_id=user_id,
        symbol=transaction.symbol,
        stock_name=stock_data.get("name"),
        currency=stock_data.get("currency"),
        quantity=transaction.quantity,
        price=current_price,  # pris fra yfinance
        # created_at sættes automatisk
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_transactions_by_user(db: Session, user_id: int):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == user_id)
        .order_by(models.Transaction.created_at.desc())
        .all()
    )


def get_portfolio_summary(db: Session, user_id: int):
    transactions = get_transactions_by_user(db, user_id)
    portfolio = {}

    for t in transactions:
        if t.symbol not in portfolio:
            portfolio[t.symbol] = {
                "symbol": t.symbol,
                "stock_name": t.stock_name,
                "currency": t.currency,
                "quantity": 0,
                "total_spent": 0,  # bruges til total invested
            }
        portfolio[t.symbol]["quantity"] += t.quantity
        portfolio[t.symbol]["total_spent"] += t.quantity * t.price

    result = []
    for sym, data in portfolio.items():
        avg_price = data["total_spent"] / data["quantity"] if data["quantity"] != 0 else 0
        stock_info = get_stock_info(sym)
        current_price = stock_info.get("price", 0)
        profit = (current_price - avg_price) * data["quantity"]

        result.append({
            "symbol": sym,
            "stock_name": data["stock_name"],
            "currency": data["currency"],
            "quantity": data["quantity"],
            "avg_buy_price": round(avg_price, 2),
            "total_invested": round(data["total_spent"], 2),
            "current_price": current_price,
            "profit": round(profit, 2)
        })

    return result
