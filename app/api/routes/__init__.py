"""
SatQuery AI - API Routes Module
"""
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.uploads import router as uploads_router
from app.api.routes.queries import router as queries_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.tools_routes import router as tools_router
from app.api.routes.models_routes import router as models_router
from app.api.routes.history import router as history_router

__all__ = [
    "auth_router",
    "health_router",
    "uploads_router",
    "queries_router",
    "analysis_router",
    "jobs_router",
    "tools_router",
    "models_router",
    "history_router",
]
