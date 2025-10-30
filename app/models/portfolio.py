from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class UserPortfolio(Base):
    __tablename__ = "user_portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(16), nullable=False, index=True)
    quantity = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)  # sum of total_amount from buys
    avg_cost = Column(Float, nullable=False, default=0.0)  # average cost per share
    current_amount = Column(Float, nullable=False, default=0.0)  # quantity * current_price
    profit = Column(Float, nullable=False, default=0.0)  # current_amount - total_amount
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")

    def __repr__(self):
        return f"<UserPortfolio user={self.user_id} symbol={self.symbol} qty={self.quantity} profit={self.profit}>"
