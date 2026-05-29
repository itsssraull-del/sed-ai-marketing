"""
SED Energy AI Marketing System — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_tables
from app.api.routes import (
    auth, content, social, analytics, stock,
    whatsapp, knowledge, media, settings as settings_router
)

logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger("sed-ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🔆 Starting SED Energy AI Marketing System...")
    await create_tables()
    logger.info("✅ Database tables ready")
    yield
    logger.info("🔌 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Autonomous AI marketing and social media operations system for SED Energy, "
        "South Africa's Tier 1 solar wholesale distributor."
    ),
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# ─── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. The team has been notified."},
    )


# ─── Routes ─────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth.router,         prefix=f"{API_PREFIX}/auth",        tags=["Authentication"])
app.include_router(content.router,      prefix=f"{API_PREFIX}/content",     tags=["Content"])
app.include_router(social.router,       prefix=f"{API_PREFIX}/social",      tags=["Social Media"])
app.include_router(analytics.router,    prefix=f"{API_PREFIX}/analytics",   tags=["Analytics"])
app.include_router(stock.router,        prefix=f"{API_PREFIX}/stock",       tags=["Stock"])
app.include_router(whatsapp.router,     prefix=f"{API_PREFIX}/whatsapp",    tags=["WhatsApp"])
app.include_router(knowledge.router,    prefix=f"{API_PREFIX}/knowledge",   tags=["Knowledge Base"])
app.include_router(media.router,        prefix=f"{API_PREFIX}/media",       tags=["Media Generation"])
app.include_router(settings_router.router, prefix=f"{API_PREFIX}/settings", tags=["Settings"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    return {
        "message": "SED Energy AI Marketing System",
        "docs": "/api/docs",
        "health": "/health",
    }
