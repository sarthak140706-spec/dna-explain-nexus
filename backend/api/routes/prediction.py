from fastapi import (
    APIRouter,
    HTTPException,
    status,
)


# ============================================================
# API schemas
# ============================================================

from backend.api.schemas.prediction import (
    PredictionResponse,
)

from backend.api.schemas.variant import (
    VariantRequest,
)


# ============================================================
# Prediction service
# ============================================================

from backend.api.services.prediction import (
    PredictionServiceError,
    predict_variant_request,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    tags=[
        "Variant Prediction",
    ],
)


# ============================================================
# Prediction endpoint
# ============================================================

@router.post(
    "/predict",
    response_model=(
        PredictionResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Predict computational "
        "variant effect"
    ),
)
def predict_variant_endpoint(
    request: VariantRequest,
) -> PredictionResponse:

    try:

        return (
            predict_variant_request(
                request
            )
        )

    except PredictionServiceError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail={
                "code": (
                    "PREDICTION_FAILED"
                ),
                "message": str(
                    error
                ),
                "research_only": True,
            },
        ) from error