from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Transaction, User
from app.schemas import transaction as transaction_schema
import yfinance as yf

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
        currency=currency
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

@router.get("/{user_id}", response_model=list[transaction_schema.TransactionRead])
def get_transactions_for_user(user_id: int, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    return transactions