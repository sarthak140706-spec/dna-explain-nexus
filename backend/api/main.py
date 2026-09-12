import sys
from pathlib import Path
from typing import (
    Any,
    Dict,
)

# ============================================================
# Make project root importable
# ============================================================

CURRENT_FILE = Path(__file__).resolve()

PROJECT_ROOT = (
    CURRENT_FILE.parents[2]
)

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

# ============================================================
# FastAPI imports
# ============================================================

from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware,
)

# ============================================================
# GeneMirror imports
# ============================================================

from backend.api.config import (
    DESCRIPTION,
    get_settings,
    verify_settings,
)

from backend.api.routes.variant import (
    router as variant_router,
)

from backend.api.routes.prediction import (
    router as prediction_router,
)

from backend.api.routes.xai import (
    router as xai_router,
)

from backend.api.routes.protein import (
    router as protein_router,
)

from backend.api.routes.scientist import (
    router as scientist_router,
)

from backend.api.routes.analysis import (
    router as analysis_router,
)

# ============================================================
# Settings
# ============================================================

settings = get_settings()

verify_settings(
    settings
)

# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=(
        f"{settings.api_prefix}/openapi.json"
    ),
)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.cors_origins
    ),
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
)

# ============================================================
# API Routers
# ============================================================

app.include_router(
    variant_router,
    prefix=settings.api_prefix,
)

app.include_router(
    prediction_router,
    prefix=settings.api_prefix,
)

app.include_router(
    xai_router,
    prefix=settings.api_prefix,
)

app.include_router(
    protein_router,
    prefix=settings.api_prefix,
)

app.include_router(
    scientist_router,
    prefix=settings.api_prefix,
)

app.include_router(
    analysis_router,
    prefix=settings.api_prefix,
)

# ============================================================
# Root Endpoint
# ============================================================

@app.get(
    "/",
    tags=[
        "System",
    ],
)
def root() -> Dict[str, Any]:

    return {
        "service": (
            settings.app_name
        ),
        "version": (
            settings.app_version
        ),
        "api_version": (
            settings.api_version
        ),
        "status": (
            "running"
        ),
        "documentation": (
            "/docs"
        ),
        "research_only": (
            settings.research_only
        ),
        "disclaimer": (
            settings.disclaimer
        ),
    }

# ============================================================
# Health Endpoint
# ============================================================

@app.get(
    f"{settings.api_prefix}/health",
    tags=[
        "System",
    ],
)
def health_check() -> Dict[str, Any]:

    return {
        "status": (
            "healthy"
        ),
        "service": (
            settings.app_name
        ),
        "version": (
            settings.app_version
        ),
        "api_version": (
            settings.api_version
        ),
        "environment": (
            settings.environment
        ),
        "research_only": (
            settings.research_only
        ),
    }

# ============================================================
# Local Runner
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=(
            settings.environment
            == "development"
        ),
    )