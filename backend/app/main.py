"""FastAPI application entrypoint for AI Video Clipper platform."""

from contextlib import asynccontextmanager
import logging
import shutil
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    admin_router,
    clips_router,
    export_router,
    jobs_router,
    media_router,
    projects_router,
    settings_router,
    upload_router,
)
from app.api.routes.settings import load_persisted_settings
from app.config import settings
from app.core.database import AsyncSessionLocal, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("clipper")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown routines."""
    logger.info("Initializing database schema...")
    await init_db()
    settings.ensure_directories()

    # Load dynamic API keys and settings from database
    async with AsyncSessionLocal() as session:
        await load_persisted_settings(session)

    logger.info(
        f"AI Video Clipper backend started on port {settings.PORT} (AI Provider: {settings.AI_PROVIDER}, Gemini Key: {'Configured' if settings.GEMINI_API_KEY else 'Missing'}, Groq Key: {'Configured' if settings.GROQ_API_KEY else 'Missing'})"
    )
    yield
    logger.info("Shutting down AI Video Clipper backend.")


app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="Production AI Video Clipping Platform Engine (GEMINI.md & Next Version Backlog)",
    lifespan=lifespan,
)

# Private Network Access (PNA) and CORS middleware for local loopback from web clients
@app.middleware("http")
async def private_network_access_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "*")
    if request.method == "OPTIONS":
        response = Response(status_code=204)
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

# CORS Configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload_router)
app.include_router(projects_router)
app.include_router(jobs_router)
app.include_router(clips_router)
app.include_router(export_router)
app.include_router(media_router)
app.include_router(admin_router)
app.include_router(settings_router)


@app.get("/api/health", tags=["Health"])
async def health_check():
    """System health check and diagnostic information."""
    ffmpeg_available = shutil.which("ffmpeg") is not None
    ffprobe_available = shutil.which("ffprobe") is not None

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "ai_provider_configured": settings.AI_PROVIDER,
        "has_gemini_key": bool(settings.GEMINI_API_KEY),
        "has_groq_key": bool(settings.GROQ_API_KEY),
        "ffmpeg_available": ffmpeg_available,
        "ffprobe_available": ffprobe_available,
    }
