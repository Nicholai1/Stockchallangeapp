from fastapi import FastAPI
from app.database import engine
from app import models
from app.routers import user as user_router
from app.routers import transaction as transaction_router
from app.services.price_updater import start_price_updater

# Opret tabeller
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Stock Portfolio API")

# Start price updater thread on startup and stop it on shutdown
@app.on_event("startup")
def _startup_event():
    thread, stop_event = start_price_updater(interval_seconds=300)
    app.state._price_updater_thread = thread
    app.state._price_updater_stop_event = stop_event


@app.on_event("shutdown")
def _shutdown_event():
    stop_event = getattr(app.state, "_price_updater_stop_event", None)
    if stop_event is not None:
        stop_event.set()

# Routers
app.include_router(user_router.router)
app.include_router(transaction_router.router)

@app.get("/")
def root():
    return {"message": "Velkommen til Stock Portfolio API"}