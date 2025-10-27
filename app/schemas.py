from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


# --- TRANSAKTIONER ---


class TransactionBase(BaseModel):
    symbol: str
    quantity: float
    price: float
    created_at: Optional[datetime] = None  # matcher models.Transaction


class TransactionCreate(BaseModel):
    symbol: str
    quantity: float


class TransactionResponse(TransactionBase):
    id: int
    stock_name: Optional[str] = None
    currency: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- BRUGERE ---

class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- PORTFØLJE ---

class PortfolioItem(BaseModel):
    symbol: str
    stock_name: Optional[str]
    quantity: float
    avg_buy_price: float
    total_invested: Optional[float] = None
    current_price: Optional[float] = None
    currency: Optional[str] = None
    profit: Optional[float] = None
