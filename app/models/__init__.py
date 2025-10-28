from app.database import Base
from app.models.user import User  # importér User-klassen direkte

__all__ = ["Base", "User"]