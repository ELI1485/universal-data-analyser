"""FastAPI application entry point.

Run with: uvicorn api.main:app --reload --port 8000
"""

import sys
from pathlib import Path

# Add project root to path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.logging_config import setup_logging
from config.settings import LOG_DIR, LOG_LEVEL

from routes.api.auth_routes import router as auth_router
from routes.api.dataset_routes import router as dataset_router
from routes.api.analytics_routes import router as analytics_router
from routes.api.report_routes import router as report_router
from routes.api.admin_routes import router as admin_router

# Initialize logging
setup_logging(log_dir=LOG_DIR, log_level=LOG_LEVEL)

app = FastAPI(
    title="Universal Data Analyzer API",
    description=(
        "REST API for the Universal Data Analyzer platform. "
        "Provides endpoints for data import, ETL, analytics, "
        "anomaly detection, AI insights, and report generation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(dataset_router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(report_router, prefix="/api/reports", tags=["Reports"])
app.include_router(admin_router, prefix="/api/admin", tags=["Administration"])


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": "Universal Data Analyzer",
        "version": "1.0.0",
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "api": "running",
    }
