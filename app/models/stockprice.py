from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.database import Base


class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(16), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=True)
    currency = Column(String(16), nullable=True)
    current_price = Column(Float, default=0.0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<StockPrice {self.symbol} {self.current_price} {self.currency}>"
