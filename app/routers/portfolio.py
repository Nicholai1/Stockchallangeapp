from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"]
)


# ------------------------------------------------------------
# 1️⃣ Opret en ny transaktion
# ------------------------------------------------------------
@router.post("/transaction", response_model=schemas.TransactionResponse)
def create_transaction(user_id: int, transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    db_transaction = crud.create_transaction(db, user_id=user_id, transaction=transaction)
    return db_transaction

#


# ------------------------------------------------------------
# 2️⃣ Hent alle transaktioner for en bruger
# ------------------------------------------------------------
@router.get("/{user_id}", response_model=List[schemas.TransactionResponse])
def get_transactions(user_id: int, db: Session = Depends(get_db)):
    transactions = crud.get_transactions_by_user(db, user_id)
    if not transactions:
        raise HTTPException(status_code=404, detail="Ingen transaktioner fundet for denne bruger")
    return transactions

#


# ------------------------------------------------------------
# 3️⃣ Hent portefølje-sammendrag
# ------------------------------------------------------------
@router.get("/{user_id}/summary", response_model=List[schemas.PortfolioItem])
def get_portfolio_summary(user_id: int, db: Session = Depends(get_db)):
    summary = crud.get_portfolio_summary(db, user_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Portefølje er tom")
    return summary
