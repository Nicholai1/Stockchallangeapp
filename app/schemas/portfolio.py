from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PortfolioItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    quantity: float
    total_amount: float
    avg_cost: float
    current_amount: float
    profit: float
    currency: Optional[str] = None
    last_updated: Optional[datetime] = None

    model_config = {"from_attributes": True}
