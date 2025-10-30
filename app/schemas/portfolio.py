from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PortfolioItem(BaseModel):
    symbol: str
    quantity: float
    total_amount: float
    avg_cost: float
    current_amount: float
    profit: float
    last_updated: Optional[datetime] = None

    model_config = {"from_attributes": True}
