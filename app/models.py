from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String, nullable=False)  # "buy" eller "sell"
    symbol = Column(String, nullable=False)
    amount = Column(int, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, default=0.0)
    currency = Column(String, nullable=False)  # Valutaenhed (f.eks. USD)
    full_name = Column(String, nullable=False)  # Aktiens fulde navn
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")


# Ensure any split-out model modules are imported so SQLAlchemy registers them with Base.metadata
try:
    import app.models.portfolio  # noqa: F401
    import app.models.stockprice  # noqa: F401
except Exception:
    # Import errors here shouldn't break app startup; they will be raised later when modules are used.
    pass