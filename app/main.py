"""
SatQuery AI - Main FastAPI Application
SIH26167: Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis
"""
import uuid
import time
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    SatQueryException,
    satquery_exception_handler,
    generic_exception_handler,
)
from app.db.database import init_db
from app.agent.registry import ToolRegistry
from app.api.routes import (
    auth_router,
    health_router,
    uploads_router,
    queries_router,
    analysis_router,
    jobs_router,
    tools_router,
    models_router,
    history_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown routines."""
    logger.info("Initializing SatQuery AI backend...")
    # Initialize Database schema
    await init_db()
    # Initialize Specialist Tool Registry & Model Adapters
    registry = ToolRegistry.get_instance()
    logger.info(f"SatQuery AI backend ready with {len(registry.list_tools())} specialist tools.")
    yield
    logger.info("Shutting down SatQuery AI backend...")


app = FastAPI(
    title="SatQuery AI Backend",
    description=(
        "Production-grade, modular, scalable backend for SIH26167: "
        "Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis. "
        "Features Single Image VQA, Visual Grounding, Bi-temporal Change Detection, and Optical + SAR Multimodal Fusion."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ------------------------------------------------------------------------------
# MIDDLEWARE
# ------------------------------------------------------------------------------

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Request ID & Observability Middleware
@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)
    
    duration = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{duration:.2f}"
    
    return response


# ------------------------------------------------------------------------------
# EXCEPTION HANDLERS
# ------------------------------------------------------------------------------
app.add_exception_handler(SatQueryException, satquery_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ------------------------------------------------------------------------------
# STATIC FILE MOUNT FOR UPLOADS & EVIDENCE
# ------------------------------------------------------------------------------
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.EVIDENCE_DIR, exist_ok=True)
app.mount("/storage/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/storage/evidence", StaticFiles(directory=settings.EVIDENCE_DIR), name="evidence")

# ------------------------------------------------------------------------------
# ROUTE INCLUSIONS
# ------------------------------------------------------------------------------
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(uploads_router, prefix=settings.API_V1_STR)
app.include_router(queries_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(tools_router, prefix=settings.API_V1_STR)
app.include_router(models_router, prefix=settings.API_V1_STR)
app.include_router(history_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }
