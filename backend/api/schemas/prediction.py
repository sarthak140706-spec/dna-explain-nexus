from typing import Optional

from pydantic import (
    BaseModel,
    Field,
)

from backend.api.schemas.variant import (
    VariantIdentity,
)


# ============================================================
# Prediction result
# ============================================================

class PredictionResult(BaseModel):

    predicted_class: int = Field(
        ge=0,
        le=1,
    )

    predicted_class_name: str

    # Sprint 4 raw model output.
    #
    # IMPORTANT:
    # This is an uncalibrated model score.
    # It is NOT confidence and NOT a clinical probability.

    raw_model_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    # These fields are intentionally optional during
    # Sprint 8 Step 4.
    #
    # Sprint 5 API integration will populate them.

    calibrated_probability: Optional[
        float
    ] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    confidence_score: Optional[
        float
    ] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    uncertainty_score: Optional[
        float
    ] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    confidence_band: Optional[
        str
    ] = None

    impact_class: Optional[
        str
    ] = None

    model_name: Optional[
        str
    ] = None

    model_version: Optional[
        str
    ] = None

    target_interpretation: Optional[
        str
    ] = None

    score_interpretation: Optional[
        str
    ] = None


# ============================================================
# Prediction response
# ============================================================

class PredictionResponse(BaseModel):

    success: bool = True

    variant: VariantIdentity

    prediction: PredictionResult

    interpretation: str

    research_only: bool = True

    disclaimer: str