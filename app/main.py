from app.routers import user as user_router
from fastapi import FastAPI
from app.database import engine
from app import models

# Dette opretter tabellerne (User osv.)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Stock Portfolio API")
app.include_router(user_router.router)

@app.get("/")
def root():
    return {"message": "Velkommen til Stock Portfolio API"}