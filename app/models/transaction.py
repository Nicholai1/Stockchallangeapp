from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import User

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(10), nullable=False)  # f.eks. BUY eller SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")  # Tilføjet currency
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relation til User
    user = relationship("User", back_populates="transactions")