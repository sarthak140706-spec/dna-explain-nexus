from fastapi import (
    APIRouter,
    HTTPException,
    status,
)


# ============================================================
# API schemas
# ============================================================

from backend.api.schemas.variant import (
    VariantRequest,
)

from backend.api.schemas.xai import (
    XAIResponse,
)


# ============================================================
# XAI service
# ============================================================

from backend.api.services.xai import (
    XAIServiceError,
    analyze_variant_xai,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    tags=[
        "Explainable AI",
    ],
)


# ============================================================
# XAI endpoint
# ============================================================

@router.post(
    "/xai",
    response_model=XAIResponse,
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Explain variant prediction "
        "with calibrated confidence"
    ),
)
def analyze_variant_xai_endpoint(
    request: VariantRequest,
) -> XAIResponse:

    try:

        return (
            analyze_variant_xai(
                request
            )
        )

    except XAIServiceError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail={
                "code": (
                    "XAI_ANALYSIS_FAILED"
                ),
                "message": str(
                    error
                ),
                "research_only": True,
            },
        ) from error