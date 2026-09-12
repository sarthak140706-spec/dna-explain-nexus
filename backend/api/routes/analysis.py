from typing import Optional

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)


# ============================================================
# Schemas
# ============================================================

from backend.api.schemas.analysis import (
    UnifiedAnalysisResponse,
)

from backend.api.schemas.variant import (
    VariantRequest,
)


# ============================================================
# Service
# ============================================================

from backend.api.services.analysis import (
    UnifiedAnalysisServiceError,
    UnifiedAnalysisValidationError,
    analyze_variant,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    tags=[
        "Unified Analysis",
    ],
)


# ============================================================
# Complete analysis endpoint
# ============================================================

@router.post(
    "/analysis",
    response_model=(
        UnifiedAnalysisResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Run the complete GeneMirror "
        "variant analysis pipeline"
    ),
)
def analysis_endpoint(
    request: VariantRequest,

    provider: Optional[str] = Query(
        default=None,
        description=(
            "Optional GeneMirror Scientist "
            "provider. When omitted or disabled, "
            "the deterministic grounded "
            "Scientist explanation is used."
        ),
    ),

) -> UnifiedAnalysisResponse:

    try:

        return analyze_variant(
            request=request,
            provider_name=provider,
        )

    except (
        UnifiedAnalysisValidationError
    ) as error:

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail={
                "code": (
                    "ANALYSIS_VARIANT_INVALID"
                ),
                "message": str(
                    error
                ),
                "research_only": True,
            },
        ) from error

    except (
        UnifiedAnalysisServiceError
    ) as error:

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "ANALYSIS_UNAVAILABLE"
                ),
                "message": str(
                    error
                ),
                "research_only": True,
            },
        ) from error