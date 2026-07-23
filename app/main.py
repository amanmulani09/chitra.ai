from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, health
from app.config import CORS_ORIGINS, logger

app = FastAPI(title="Chitra.ai AI video analysis app", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router)
app.include_router(analyze.router)

logger.info("Chitra.ai app initialized")
