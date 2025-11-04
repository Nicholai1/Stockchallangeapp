from fastapi import FastAPI
import asyncio
from fastapi.staticfiles import StaticFiles
from app.database import engine
from app import models
from app.routers import user as user_router
from app.routers import transaction as transaction_router
from app.routers import portfolio as portfolio_router
from app.routers import auth as auth_router
from app.routers import stocks as stocks_router
from app.services.price_updater import start_price_updater
from app.routers import symbols as symbols_router
from app.services import ws_manager
from app.routers import ws as ws_router
from app.routers import admin as admin_router

# Opret tabeller
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Stock Portfolio API")

# Start price updater thread on startup and stop it on shutdown
@app.on_event("startup")
async def _startup_event():
    # initialize websocket manager (queue + broadcaster task)
    loop = asyncio.get_event_loop()
    await ws_manager.init(loop)
    # start price updater thread
    # For local testing it's convenient to run the updater frequently.
    # Use 10s here; increase in production to a larger value (e.g. 300s).
    thread, stop_event = start_price_updater(interval_seconds=60)
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
app.include_router(portfolio_router.router)
app.include_router(auth_router.router)
app.include_router(stocks_router.router)
app.include_router(ws_router.router)
app.include_router(symbols_router.router)
app.include_router(admin_router.router)

# Serve the static frontend at /app
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/")
def root():
    return {"message": "Velkommen til Stock Portfolio API"}