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

from backend.api.schemas.variant import (
    VariantRequest,
)

from backend.api.schemas.scientist import (
    ScientistResponse,
)


# ============================================================
# Service
# ============================================================

from backend.api.services.scientist import (
    ScientistServiceError,
    ScientistVariantValidationError,
    analyze_variant_with_scientist,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    tags=[
        "GeneMirror Scientist",
    ],
)


# ============================================================
# Scientist endpoint
# ============================================================

@router.post(
    "/scientist",
    response_model=(
        ScientistResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Generate a grounded GeneMirror "
        "Scientist explanation"
    ),
)
def scientist_endpoint(
    request: VariantRequest,

    provider: Optional[str] = Query(
        default=None,
        description=(
            "Optional Scientist provider. "
            "When omitted or disabled, "
            "GeneMirror uses its deterministic "
            "grounded explanation fallback."
        ),
    ),

) -> ScientistResponse:

    try:

        return (
            analyze_variant_with_scientist(
                request=request,
                provider_name=provider,
            )
        )

    except (
        ScientistVariantValidationError
    ) as error:

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail={
                "code": (
                    "SCIENTIST_VARIANT_INVALID"
                ),
                "message": str(
                    error
                ),
                "research_only": True,
            },
        ) from error

    except (
        ScientistServiceError
    ) as error:

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "SCIENTIST_UNAVAILABLE"
                ),
                "message": str(
                    error
                ),
                "research_only": True,
            },
        ) from error