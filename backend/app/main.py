"""
DocGuard AI — FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models.schemas import HealthResponse
from .routes import repositories, analysis, documentation

# ---------------------------------------------------------------- logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("docguard")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("DocGuard AI backend starting")
    yield
    logger.info("DocGuard AI backend shutting down")


app = FastAPI(
    title="DocGuard AI",
    description="Autonomous API Documentation Agent — backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------- CORS
# Covers the common local Vite dev-server ports. Adjust origins freely.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------- routers
app.include_router(repositories.router)
app.include_router(analysis.router)
app.include_router(documentation.router)


# ---------------------------------------------------------------- health

@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    logger.debug("Health check hit")
    return HealthResponse(status="ok", service="DocGuard AI")