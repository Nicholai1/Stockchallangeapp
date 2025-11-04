from pydantic import BaseModel, Field
from datetime import datetime


class TransactionCreate(BaseModel):
    user_id: int
    symbol: str = Field(..., min_length=1, max_length=10)
    # accept both 'name' and frontend 'full_name' via alias
    name: str = Field(..., min_length=1, max_length=100, alias="full_name")
    type: str = Field(..., min_length=3, max_length=10)
    # accept both 'quantity' and frontend 'amount' via alias
    quantity: float = Field(..., alias="amount")
    price: float
    currency: str = Field(..., min_length=1, max_length=10)

    model_config = {
        # allow populating by field name as well as by alias
        "populate_by_name": True,
        "from_attributes": True,
    }


class TransactionRead(BaseModel):
    id: int
    user_id: int
    symbol: str
    name: str
    type: str
    quantity: float
    price: float
    total_amount: float
    currency: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class TransactionUpdate(BaseModel):
    user_id: int
    quantity: float = Field(..., alias="amount")
    price: float

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
    }