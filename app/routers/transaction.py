from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Transaction, User
from app.models import StockPrice
from app.schemas import transaction as transaction_schema
import yfinance as yf
from app.services.stocks import get_stock_info
from app.services.price_updater import recompute_portfolios_for_symbol

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

@router.post("/", response_model=transaction_schema.TransactionRead)
def create_transaction(transaction_in: transaction_schema.TransactionCreate, db: Session = Depends(get_db)):
    # Tjek om user findes
    user = db.query(User).filter(User.id == transaction_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Hent selskabsinfo fra Yahoo Finance
    ticker = yf.Ticker(transaction_in.symbol)
    info = ticker.info
    company_name = info.get("longName") or transaction_in.symbol
    currency = info.get("currency") or transaction_in.currency

    new_transaction = Transaction(
        user_id=transaction_in.user_id,
        symbol=transaction_in.symbol,
        name=company_name,
        type=transaction_in.type,
        quantity=transaction_in.quantity,
        price=transaction_in.price,
        total_amount=transaction_in.quantity * transaction_in.price,
        currency=currency
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    # Hvis ticker ikke findes i StockPrice, indsæt den med nuværende pris
    existing = db.query(StockPrice).filter(StockPrice.symbol == new_transaction.symbol).first()
    if not existing:
        info = get_stock_info(new_transaction.symbol)
        sp = StockPrice(
            symbol=new_transaction.symbol,
            name=info.get("name"),
            currency=info.get("currency"),
            current_price=info.get("price", 0),
        )
        db.add(sp)
        db.commit()
        db.refresh(sp)
        # Recompute portfolios immediately for the inserted symbol so new transactions show up
        try:
            recompute_portfolios_for_symbol(db, new_transaction.symbol)
            db.commit()
        except Exception:
            # don't fail the transaction creation if recompute fails; log instead
            pass
    else:
        # If the symbol already existed, still recompute portfolios so new transaction shows up immediately
        try:
            recompute_portfolios_for_symbol(db, new_transaction.symbol)
            db.commit()
        except Exception:
            pass
    # Return a validated Pydantic model instance to avoid response validation issues
    return transaction_schema.TransactionRead.model_validate(new_transaction)

@router.get("/{user_id}", response_model=list[transaction_schema.TransactionRead])
def get_transactions_for_user(user_id: int, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    return transactions