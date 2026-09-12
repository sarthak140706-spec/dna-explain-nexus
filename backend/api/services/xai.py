from typing import (
    Any,
    Dict,
)


# ============================================================
# Frozen Sprint 5 engines
# ============================================================

from backend.explainability.contribution_normalizer import (
    build_normalized_explanation,
)

from backend.explainability.impact_mapper import (
    evaluate_variant_impact,
)


# ============================================================
# Sprint 8 adapters
# ============================================================

from backend.api.services.prediction import (
    build_model_input,
    build_prediction_variant_identity,
)


# ============================================================
# API schemas
# ============================================================

from backend.api.schemas.variant import (
    VariantRequest,
)

from backend.api.schemas.xai import (
    DirectionSummaryResponse,
    LocalExplanationResponse,
    XAIResponse,
    XAIResult,
)


# ============================================================
# Constants
# ============================================================

RESEARCH_DISCLAIMER = (
    "GeneMirror AI provides computational predictions "
    "for research and educational purposes only. "
    "It does not provide clinical diagnosis, treatment "
    "recommendations, or medical advice."
)


RAW_SCORE_TOLERANCE = 1e-12


# ============================================================
# Service exception
# ============================================================

class XAIServiceError(
    RuntimeError
):
    """
    Raised when the frozen Sprint 5 explainability,
    calibration, confidence, or impact engines
    cannot complete analysis.
    """


# ============================================================
# Direction summary adapter
# ============================================================

def build_direction_summary(
    payload: Dict[str, Any],
) -> DirectionSummaryResponse:

    summary = payload.get(
        "direction_summary",
        {},
    )

    return DirectionSummaryResponse(
        supporting_higher_impact_percent=float(
            summary.get(
                "supporting_higher_impact_percent",
                0.0,
            )
        ),
        supporting_lower_impact_percent=float(
            summary.get(
                "supporting_lower_impact_percent",
                0.0,
            )
        ),
        neutral_percent=float(
            summary.get(
                "neutral_percent",
                0.0,
            )
        ),
        total_percent=float(
            summary.get(
                "total_percent",
                0.0,
            )
        ),
    )


# ============================================================
# Local explanation adapter
# ============================================================

def build_local_explanation_result(
    payload: Dict[str, Any],
) -> LocalExplanationResponse:

    return LocalExplanationResponse(
        normalization_version=(
            payload.get(
                "normalization_version"
            )
        ),
        explanation_version=(
            payload.get(
                "explanation_version"
            )
        ),
        model_name=(
            payload.get(
                "model_name"
            )
        ),
        model_version=(
            payload.get(
                "model_version"
            )
        ),
        target_interpretation=(
            payload.get(
                "target_interpretation"
            )
        ),
        normalization_method=(
            payload.get(
                "normalization_method"
            )
        ),
        normalization_formula=(
            payload.get(
                "normalization_formula"
            )
        ),
        total_absolute_contribution=float(
            payload.get(
                "total_absolute_contribution",
                0.0,
            )
        ),
        feature_count=int(
            payload.get(
                "feature_count",
                0,
            )
        ),
        feature_contributions=(
            payload.get(
                "feature_contributions",
                [],
            )
        ),
        top_features=(
            payload.get(
                "top_features",
                [],
            )
        ),
        direction_summary=(
            build_direction_summary(
                payload
            )
        ),
        percentage_interpretation=(
            payload.get(
                "percentage_interpretation",
                (
                    "Normalized percentages describe "
                    "relative local perturbation "
                    "magnitude and are not causal "
                    "biological importance."
                ),
            )
        ),
        test_set_used=bool(
            payload.get(
                "test_set_used",
                False,
            )
        ),
        research_only=bool(
            payload.get(
                "research_only",
                True,
            )
        ),
    )


# ============================================================
# Impact / confidence adapter
# ============================================================

def build_xai_result(
    impact_result: Dict[str, Any],
) -> XAIResult:

    return XAIResult(
        predicted_class=int(
            impact_result[
                "predicted_class"
            ]
        ),
        predicted_class_name=str(
            impact_result[
                "predicted_class_name"
            ]
        ),
        raw_model_score=float(
            impact_result[
                "raw_model_score"
            ]
        ),
        calibrated_probability=float(
            impact_result[
                "calibrated_probability"
            ]
        ),
        confidence_score=float(
            impact_result[
                "confidence_score"
            ]
        ),
        uncertainty_score=float(
            impact_result[
                "uncertainty_score"
            ]
        ),
        confidence_band=str(
            impact_result[
                "confidence_band"
            ]
        ),
        impact_class=str(
            impact_result[
                "impact_class"
            ]
        ),
        calibration_version=(
            impact_result.get(
                "calibration_version"
            )
        ),
        confidence_version=(
            impact_result.get(
                "confidence_version"
            )
        ),
        impact_mapping_version=(
            impact_result.get(
                "impact_mapping_version"
            )
        ),
        confidence_method=(
            impact_result.get(
                "confidence_method"
            )
        ),
        uncertainty_method=(
            impact_result.get(
                "uncertainty_method"
            )
        ),
        probability_interpretation=(
            impact_result.get(
                "probability_interpretation"
            )
        ),
        confidence_interpretation=(
            impact_result.get(
                "confidence_interpretation"
            )
        ),
        uncertainty_interpretation=(
            impact_result.get(
                "uncertainty_interpretation"
            )
        ),
        impact_interpretation=(
            impact_result.get(
                "impact_interpretation"
            )
        ),
    )


# ============================================================
# Cross-engine consistency verification
# ============================================================

def verify_xai_consistency(
    impact_result: Dict[str, Any],
    explanation_payload: Dict[str, Any],
) -> None:
    """
    Ensure Sprint 5 impact analysis and local XAI
    refer to the same frozen Sprint 4 prediction.
    """

    impact_score = float(
        impact_result[
            "raw_model_score"
        ]
    )

    explanation_score = float(
        explanation_payload[
            "raw_model_score"
        ]
    )

    if (
        abs(
            impact_score
            - explanation_score
        )
        > RAW_SCORE_TOLERANCE
    ):

        raise XAIServiceError(
            "Sprint 5 consistency check failed: "
            "impact engine and local explanation "
            "returned different raw model scores."
        )

    impact_class_prediction = int(
        impact_result[
            "predicted_class"
        ]
    )

    explanation_class_prediction = int(
        explanation_payload[
            "predicted_class"
        ]
    )

    if (
        impact_class_prediction
        != explanation_class_prediction
    ):

        raise XAIServiceError(
            "Sprint 5 consistency check failed: "
            "impact engine and local explanation "
            "returned different predicted classes."
        )

    if bool(
        explanation_payload.get(
            "test_set_used",
            False,
        )
    ):

        raise XAIServiceError(
            "Local explanation unexpectedly "
            "indicates test-set usage."
        )


# ============================================================
# Main XAI service
# ============================================================

def analyze_variant_xai(
    request: VariantRequest,
) -> XAIResponse:

    variant_identity = (
        build_prediction_variant_identity(
            request
        )
    )

    model_input = (
        build_model_input(
            request
        )
    )

    try:

        # ----------------------------------------------------
        # Calibration + confidence + uncertainty + impact
        # ----------------------------------------------------

        impact_result = (
            evaluate_variant_impact(
                model_input
            )
        )

        # ----------------------------------------------------
        # Local normalized XAI
        # ----------------------------------------------------

        explanation_payload = (
            build_normalized_explanation(
                model_input
            )
        )

        # ----------------------------------------------------
        # Cross-engine verification
        # ----------------------------------------------------

        verify_xai_consistency(
            impact_result=(
                impact_result
            ),
            explanation_payload=(
                explanation_payload
            ),
        )

    except XAIServiceError:

        raise

    except (
        ValueError,
        FileNotFoundError,
        KeyError,
    ) as error:

        raise XAIServiceError(
            "Sprint 5 analysis failed: "
            f"{error}"
        ) from error

    except Exception as error:

        raise XAIServiceError(
            "Explainability engine failed: "
            f"{error}"
        ) from error

    result = (
        build_xai_result(
            impact_result
        )
    )

    explanation = (
        build_local_explanation_result(
            explanation_payload
        )
    )

    return XAIResponse(
        success=True,
        variant=(
            variant_identity
        ),
        result=result,
        explanation=explanation,
        research_only=True,
        disclaimer=(
            RESEARCH_DISCLAIMER
        ),
    )