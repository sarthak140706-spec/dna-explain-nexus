from typing import (
    Any,
    Dict,
)


# ============================================================
# Frozen Sprint 4 prediction engine
# ============================================================

from backend.modeling.predictor import (
    predict_variant,
)


# ============================================================
# API schemas
# ============================================================

from backend.api.schemas.prediction import (
    PredictionResponse,
    PredictionResult,
)

from backend.api.schemas.variant import (
    VariantIdentity,
    VariantRequest,
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


# ============================================================
# Service exception
# ============================================================

class PredictionServiceError(
    RuntimeError
):
    """
    Raised when the frozen Sprint 4 prediction
    engine cannot complete inference.
    """


# ============================================================
# Variant identity
# ============================================================

def build_prediction_variant_identity(
    request: VariantRequest,
) -> VariantIdentity:

    return VariantIdentity(
        gene_symbol=(
            request.gene_symbol
        ),
        chromosome=(
            request.chromosome
        ),
        position=(
            request.position
        ),
        reference_allele=(
            request.reference_allele
        ),
        alternate_allele=(
            request.alternate_allele
        ),
        protein_position=(
            request.protein_position
        ),
        reference_amino_acid=(
            request.reference_amino_acid
        ),
        alternate_amino_acid=(
            request.alternate_amino_acid
        ),
        dna_change=(
            request.dna_change
        ),
        protein_change=(
            request.protein_change
        ),
    )


# ============================================================
# Sprint 4 input adapter
# ============================================================

def build_model_input(
    request: VariantRequest,
) -> Dict[str, Any]:
    """
    Convert the public API contract into the exact
    field names expected by the frozen Sprint 4
    predictor.

    API:
        reference_amino_acid
        alternate_amino_acid

    Sprint 4:
        reference_aa
        alternate_aa
    """

    return {
        "reference_allele": (
            request.reference_allele
        ),
        "alternate_allele": (
            request.alternate_allele
        ),
        "reference_aa": (
            request.reference_amino_acid
        ),
        "alternate_aa": (
            request.alternate_amino_acid
        ),
        "protein_position": (
            request.protein_position
        ),
    }


# ============================================================
# Prediction result adapter
# ============================================================

def build_prediction_result(
    result: Dict[str, Any],
) -> PredictionResult:
    """
    Adapt the frozen Sprint 4 result to the
    stable Sprint 8 API contract.

    model_score is deliberately renamed to
    raw_model_score at the API boundary so
    consumers do not confuse it with calibrated
    probability or confidence.
    """

    return PredictionResult(
        predicted_class=(
            result[
                "predicted_class"
            ]
        ),
        predicted_class_name=(
            result[
                "predicted_class_name"
            ]
        ),
        raw_model_score=(
            result[
                "model_score"
            ]
        ),
        calibrated_probability=None,
        confidence_score=None,
        uncertainty_score=None,
        confidence_band=None,
        impact_class=None,
        model_name=(
            result.get(
                "model_name"
            )
        ),
        model_version=(
            result.get(
                "model_version"
            )
        ),
        target_interpretation=(
            result.get(
                "target_interpretation"
            )
        ),
        score_interpretation=(
            result.get(
                "score_interpretation"
            )
        ),
    )


# ============================================================
# Main prediction service
# ============================================================

def predict_variant_request(
    request: VariantRequest,
) -> PredictionResponse:

    variant = (
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

        raw_result = (
            predict_variant(
                model_input
            )
        )

    except (
        ValueError,
        FileNotFoundError,
    ) as error:

        raise PredictionServiceError(
            "Variant prediction failed: "
            f"{error}"
        ) from error

    except Exception as error:

        raise PredictionServiceError(
            "Prediction engine failed: "
            f"{error}"
        ) from error

    prediction = (
        build_prediction_result(
            raw_result
        )
    )

    return PredictionResponse(
        success=True,
        variant=variant,
        prediction=prediction,
        interpretation=(
            raw_result.get(
                "target_interpretation",
                (
                    "ClinVar-derived pathogenicity "
                    "proxy for computational "
                    "variant-effect modeling."
                ),
            )
        ),
        research_only=True,
        disclaimer=(
            RESEARCH_DISCLAIMER
        ),
    )