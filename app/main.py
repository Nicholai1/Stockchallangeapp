from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine

# Importér routers
from .routers import portfolio

# ------------------------------------------------------------
# Initialiser database
# ------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ------------------------------------------------------------
# Opret FastAPI app
# ------------------------------------------------------------
app = FastAPI(
    title="MyStock Portfolio API",
    description="En simpel FastAPI app til at følge dine egne aktier",
    version="0.2.0",
)

# ------------------------------------------------------------
# CORS setup
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Inkludér routers
# ------------------------------------------------------------
app.include_router(portfolio.router)


# ------------------------------------------------------------
# Root endpoint
# ------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Velkommen til MyStock Portfolio API 🚀"}
