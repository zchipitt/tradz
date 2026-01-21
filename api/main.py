"""
FastAPI application entry point for Tradz API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routers import signals_router, sources_router, reports_router, events_router, system_router

settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.api_version,
    }


# Include routers
app.include_router(signals_router, prefix="/api/signals", tags=["signals"])
app.include_router(sources_router, prefix="/api/sources", tags=["sources"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(events_router, prefix="/api/events", tags=["events"])
app.include_router(system_router, prefix="/api/system", tags=["system"])


@app.get("/")
async def root():
    """Root endpoint redirects to API docs."""
    return {
        "message": "Welcome to Tradz API",
        "docs": "/api/docs",
        "health": "/api/health",
    }
