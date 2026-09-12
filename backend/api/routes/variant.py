from fastapi import (
    APIRouter,
    HTTPException,
    status,
)


from backend.api.schemas.variant import (
    VariantRequest,
    VariantValidationResponse,
)

from backend.api.services.variant_validation import (
    VariantValidationServiceError,
    validate_variant_request,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/variants",
    tags=[
        "Variant Validation",
    ],
)


# ============================================================
# Variant validation endpoint
# ============================================================

@router.post(
    "/validate",
    response_model=(
        VariantValidationResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Validate a GeneMirror "
        "missense variant"
    ),
)
def validate_variant(
    request: VariantRequest,
) -> VariantValidationResponse:

    try:

        return (
            validate_variant_request(
                request
            )
        )

    except VariantValidationServiceError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "SCIENTIFIC_SERVICE_UNAVAILABLE"
                ),
                "message": str(
                    error
                ),
                "research_only": True,
            },
        ) from error