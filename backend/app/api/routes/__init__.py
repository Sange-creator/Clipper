"""API routes package."""

from app.api.routes.admin import router as admin_router
from app.api.routes.clips import router as clips_router
from app.api.routes.export import router as export_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.media import router as media_router
from app.api.routes.projects import router as projects_router
from app.api.routes.settings import router as settings_router
from app.api.routes.upload import router as upload_router

__all__ = [
    "upload_router",
    "projects_router",
    "jobs_router",
    "clips_router",
    "export_router",
    "media_router",
    "admin_router",
    "settings_router",
]
