import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


# ============================================================
# Project paths
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
API_DIR = CURRENT_FILE.parent
BACKEND_DIR = API_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent


# ============================================================
# API metadata
# ============================================================

APP_NAME = "GeneMirror AI"
APP_VERSION = "1.0.0"
API_VERSION = "v1"

API_PREFIX = f"/api/{API_VERSION}"

DESCRIPTION = (
    "GeneMirror AI computational variant-analysis API. "
    "The service provides research and educational "
    "outputs for missense genetic variants using "
    "variant validation, machine learning, explainable "
    "AI, confidence estimation, protein context, and "
    "the GeneMirror Scientist explanation layer."
)

RESEARCH_DISCLAIMER = (
    "GeneMirror AI provides computational predictions "
    "for research and educational purposes only. "
    "It does not provide clinical diagnosis, treatment "
    "recommendations, or medical advice."
)


# ============================================================
# Environment helpers
# ============================================================

def get_environment() -> str:
    return os.getenv(
        "GENEMIRROR_ENV",
        "development",
    ).strip().lower()


def get_host() -> str:
    return os.getenv(
        "GENEMIRROR_API_HOST",
        "127.0.0.1",
    ).strip()


def get_port() -> int:
    raw_port = os.getenv(
        "PORT",
        os.getenv(
            "GENEMIRROR_API_PORT",
            "8000",
        ),
    )

    try:
        port = int(raw_port)

    except ValueError as exc:
        raise ValueError(
            "GENEMIRROR_API_PORT/PORT must "
            "contain a valid integer."
        ) from exc

    if not 1 <= port <= 65535:
        raise ValueError(
            "API port must be between "
            "1 and 65535."
        )

    return port


def get_cors_origins() -> List[str]:

    configured = os.getenv(
        "GENEMIRROR_CORS_ORIGINS",
        "",
    ).strip()

    if configured:

        origins = [
            item.strip()
            for item in configured.split(",")
            if item.strip()
        ]

        return origins

    # Development defaults.
    return [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


# ============================================================
# Settings object
# ============================================================

@dataclass(frozen=True)
class APISettings:
    app_name: str
    app_version: str
    api_version: str
    api_prefix: str
    environment: str
    host: str
    port: int
    cors_origins: List[str]
    research_only: bool
    disclaimer: str


def get_settings() -> APISettings:

    return APISettings(
        app_name=APP_NAME,
        app_version=APP_VERSION,
        api_version=API_VERSION,
        api_prefix=API_PREFIX,
        environment=get_environment(),
        host=get_host(),
        port=get_port(),
        cors_origins=get_cors_origins(),
        research_only=True,
        disclaimer=RESEARCH_DISCLAIMER,
    )


# ============================================================
# Configuration verification
# ============================================================

def verify_settings(
    settings: APISettings,
) -> None:

    if not settings.app_name:
        raise ValueError(
            "Application name cannot be empty."
        )

    if not settings.api_prefix.startswith(
        "/api/"
    ):
        raise ValueError(
            "API prefix must start with /api/."
        )

    if not settings.environment:
        raise ValueError(
            "Environment cannot be empty."
        )

    if not 1 <= settings.port <= 65535:
        raise ValueError(
            "Invalid API port."
        )

    if settings.research_only is not True:
        raise ValueError(
            "GeneMirror API must remain "
            "research-only."
        )

    if not settings.disclaimer.strip():
        raise ValueError(
            "Research disclaimer is required."
        )


if __name__ == "__main__":

    settings = get_settings()
    verify_settings(settings)

    print(
        "GeneMirror API Configuration"
    )
    print("=" * 60)

    print(
        "App:",
        settings.app_name,
    )

    print(
        "Version:",
        settings.app_version,
    )

    print(
        "API version:",
        settings.api_version,
    )

    print(
        "API prefix:",
        settings.api_prefix,
    )

    print(
        "Environment:",
        settings.environment,
    )

    print(
        "Host:",
        settings.host,
    )

    print(
        "Port:",
        settings.port,
    )

    print(
        "CORS origins:",
        settings.cors_origins,
    )

    print(
        "Research only:",
        settings.research_only,
    )

    print(
        "\n✅ API configuration verification completed."
    )