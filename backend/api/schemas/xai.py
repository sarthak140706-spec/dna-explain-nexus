from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

from backend.api.schemas.variant import (
    VariantIdentity,
)


# ============================================================
# Direction summary
# ============================================================

class DirectionSummaryResponse(BaseModel):

    supporting_higher_impact_percent: float = Field(
        ge=0.0,
        le=100.0,
    )

    supporting_lower_impact_percent: float = Field(
        ge=0.0,
        le=100.0,
    )

    neutral_percent: float = Field(
        ge=0.0,
        le=100.0,
    )

    total_percent: float = Field(
        ge=0.0,
    )


# ============================================================
# Normalized local explanation
# ============================================================

class LocalExplanationResponse(BaseModel):

    normalization_version: Optional[
        str
    ] = None

    explanation_version: Optional[
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

    normalization_method: Optional[
        str
    ] = None

    normalization_formula: Optional[
        str
    ] = None

    total_absolute_contribution: float = Field(
        ge=0.0,
    )

    feature_count: int = Field(
        ge=0,
    )

    # Sprint 5 owns the exact feature-level
    # explanation contract.
    #
    # We deliberately preserve each frozen
    # contribution dictionary rather than
    # redefining its scientific fields here.

    feature_contributions: List[
        Dict[str, Any]
    ]

    top_features: List[
        Dict[str, Any]
    ]

    direction_summary: (
        DirectionSummaryResponse
    )

    percentage_interpretation: str

    test_set_used: bool

    research_only: bool


# ============================================================
# XAI + confidence result
# ============================================================

class XAIResult(BaseModel):

    predicted_class: int = Field(
        ge=0,
        le=1,
    )

    predicted_class_name: str

    # --------------------------------------------------------
    # Semantic separation
    # --------------------------------------------------------
    #
    # These four values must remain distinct.
    #
    # raw_model_score:
    #     Sprint 4 uncalibrated output.
    #
    # calibrated_probability:
    #     calibrated probability of the
    #     ClinVar-derived pathogenic-like proxy.
    #
    # confidence_score:
    #     entropy-derived decision decisiveness.
    #
    # uncertainty_score:
    #     normalized binary entropy.
    # --------------------------------------------------------

    raw_model_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    calibrated_probability: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    uncertainty_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_band: str

    impact_class: str

    calibration_version: Optional[
        str
    ] = None

    confidence_version: Optional[
        str
    ] = None

    impact_mapping_version: Optional[
        str
    ] = None

    confidence_method: Optional[
        str
    ] = None

    uncertainty_method: Optional[
        str
    ] = None

    probability_interpretation: Optional[
        str
    ] = None

    confidence_interpretation: Optional[
        str
    ] = None

    uncertainty_interpretation: Optional[
        str
    ] = None

    impact_interpretation: Optional[
        str
    ] = None


# ============================================================
# Complete endpoint response
# ============================================================

class XAIResponse(BaseModel):

    success: bool = True

    variant: VariantIdentity

    result: XAIResult

    explanation: LocalExplanationResponse

    research_only: bool = True

    disclaimer: str