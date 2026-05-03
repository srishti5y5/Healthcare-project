"""
app/main.py
FastAPI application factory — the entrypoint for uvicorn.

Run with:
    uvicorn app.main:app --reload --port 8000
"""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.init_db import init_db


# ── Lifespan: runs on startup and shutdown ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("⏳  Initialising database tables …")
    await init_db()
    print("✅  Database ready.")
    yield
    # Shutdown (add cleanup here if needed)
    print("🔴  Shutting down.")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Healthcare Access Inequality Map — API",
    description=(
        "Production-grade REST API for exploring district-level healthcare "
        "inequalities across India using ML-powered risk scoring."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # In production, log to Sentry / CloudWatch here
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred.", "type": type(exc).__name__},
    )


# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health():
    """Quick liveness probe for load balancers / Docker HEALTHCHECK."""
    return {"status": "ok", "version": "1.0.0"}
