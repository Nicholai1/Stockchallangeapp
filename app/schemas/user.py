from pydantic import BaseModel, Field
from datetime import datetime

# Input schema når vi opretter en bruger
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

# Output schema når vi returnerer en bruger
class UserRead(BaseModel):
    id: int
    username: str
    created_at: datetime  # Brug datetime i stedet for str

    model_config = {
        "from_attributes": True  # erstatter orm_mode
    }