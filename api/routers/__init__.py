"""
API routers package.
"""
from .briefs import router as briefs_router
from .events import router as events_router
from .reports import router as reports_router
from .signals import router as signals_router
from .sources import router as sources_router
from .system import router as system_router

__all__ = ["signals_router", "sources_router", "reports_router", "events_router", "system_router", "briefs_router"]
