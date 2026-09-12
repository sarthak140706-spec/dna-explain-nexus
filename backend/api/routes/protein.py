from fastapi import (
    APIRouter,
    HTTPException,
    status,
)


# ============================================================
# Schemas
# ============================================================

from backend.api.schemas.variant import (
    VariantRequest,
)

from backend.api.schemas.protein import (
    ProteinContextResponse,
)


# ============================================================
# Service
# ============================================================

from backend.api.services.protein import (
    ProteinContextServiceError,
    ProteinContextValidationError,
    analyze_protein_context,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    tags=[
        "Protein Context",
    ],
)


# ============================================================
# Protein-context endpoint
# ============================================================

@router.post(
    "/protein-context",
    response_model=(
        ProteinContextResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Generate protein context and "
        "visualization data for a variant"
    ),
)
def protein_context_endpoint(
    request: VariantRequest,
) -> ProteinContextResponse:

    try:

        return analyze_protein_context(
            request
        )

    except (
        ProteinContextValidationError
    ) as error:

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail={
                "code": (
                    "PROTEIN_VARIANT_INVALID"
                ),
                "message": str(
                    error
                ),
                "research_only": True,
            },
        ) from error

    except (
        ProteinContextServiceError
    ) as error:

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "PROTEIN_CONTEXT_UNAVAILABLE"
                ),
                "message": str(
                    error
                ),
                "research_only": True,
            },
        ) from error