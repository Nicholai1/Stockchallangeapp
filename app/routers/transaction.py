from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Transaction, User
from app.models import StockPrice
from app.schemas import transaction as transaction_schema
from app.services.price_updater import recompute_portfolios_for_symbol
from app.schemas.transaction import TransactionUpdate

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

    # Use local metadata if available; avoid network calls here to prevent rate limits.
    existing_sp = db.query(StockPrice).filter(StockPrice.symbol == transaction_in.symbol).first()
    name = transaction_in.name if hasattr(transaction_in, 'name') else transaction_in.symbol
    currency = transaction_in.currency

    # If we have a StockPrice row, prefer its name/currency
    if existing_sp:
        if existing_sp.name:
            name = existing_sp.name
        if existing_sp.currency:
            currency = existing_sp.currency

    new_transaction = Transaction(
        user_id=transaction_in.user_id,
        symbol=transaction_in.symbol,
        name=name,
        type=transaction_in.type,
        quantity=transaction_in.quantity,
        price=transaction_in.price,
        total_amount=transaction_in.quantity * transaction_in.price,
        currency=currency
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    # If ticker doesn't exist in StockPrice, insert a lightweight row (no network calls)
    existing = db.query(StockPrice).filter(StockPrice.symbol == new_transaction.symbol).first()
    if not existing:
        sp = StockPrice(
            symbol=new_transaction.symbol,
            name=new_transaction.name,
            currency=new_transaction.currency,
            current_price=0.0,
        )
        db.add(sp)
        db.commit()
        db.refresh(sp)

    # Recompute portfolios for the symbol so user's portfolio reflects the new transaction
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



@router.put("/{transaction_id}", response_model=transaction_schema.TransactionRead)
def update_transaction(transaction_id: int, update: TransactionUpdate, db: Session = Depends(get_db)):
    t = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if t.user_id != update.user_id:
        raise HTTPException(status_code=403, detail="Not allowed to modify this transaction")

    # apply changes
    t.quantity = update.quantity
    t.price = update.price
    t.total_amount = update.quantity * update.price
    db.add(t)
    db.commit()
    db.refresh(t)

    # recompute portfolios for this symbol
    try:
        recompute_portfolios_for_symbol(db, t.symbol)
        db.commit()
    except Exception:
        pass

    return transaction_schema.TransactionRead.model_validate(t)


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, user_id: int, db: Session = Depends(get_db)):
    t = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if t.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this transaction")

    symbol = t.symbol
    db.delete(t)
    db.commit()

    # recompute portfolios for this symbol
    try:
        recompute_portfolios_for_symbol(db, symbol)
        db.commit()
    except Exception:
        pass

    return {"detail": "deleted"}