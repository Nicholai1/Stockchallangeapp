from pydantic import BaseModel, Field

class TransactionCreate(BaseModel):
    user_id: int
    symbol: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=3, max_length=10)
    quantity: float
    price: float
    currency: str = Field(..., min_length=1, max_length=10)

class TransactionRead(BaseModel):
    id: int
    user_id: int
    symbol: str
    name: str
    type: str
    quantity: float
    price: float
    currency: str
    created_at: str

    model_config = {
        "from_attributes": True
    }