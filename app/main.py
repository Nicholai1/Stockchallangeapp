from fastapi import FastAPI
from app.database import engine
from app import models
from app.routers import user as user_router
from app.routers import transaction as transaction_router

# Opret tabeller
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Stock Portfolio API")

# Routers
app.include_router(user_router.router)
app.include_router(transaction_router.router)

@app.get("/")
def root():
    return {"message": "Velkommen til Stock Portfolio API"}