from typing import Optional


# ============================================================
# API schemas
# ============================================================

from backend.api.schemas.analysis import (
    UnifiedAnalysisResponse,
)

from backend.api.schemas.prediction import (
    PredictionResult,
)

from backend.api.schemas.variant import (
    VariantRequest,
)


# ============================================================
# Existing Sprint 8 services
# ============================================================

from backend.api.services.variant_validation import (
    VariantValidationServiceError,
    validate_variant_request,
)

from backend.api.services.xai import (
    XAIServiceError,
    analyze_variant_xai,
)

from backend.api.services.protein import (
    ProteinContextServiceError,
    ProteinContextValidationError,
    analyze_protein_context,
)

from backend.api.services.scientist import (
    ScientistServiceError,
    ScientistVariantValidationError,
    analyze_variant_with_scientist,
)

from backend.api.services.prediction import (
    build_prediction_variant_identity,
)


# ============================================================
# Research disclaimer
# ============================================================

RESEARCH_DISCLAIMER = (
    "GeneMirror AI provides computational "
    "predictions, explanations, and "
    "protein-context information for research "
    "and educational purposes only. It is not "
    "intended for clinical diagnosis, treatment "
    "decisions, or medical advice."
)


# ============================================================
# Unified-service exceptions
# ============================================================

class UnifiedAnalysisValidationError(
    ValueError
):
    """
    Raised when a variant fails a scientific
    validation requirement needed for the
    complete GeneMirror analysis.
    """


class UnifiedAnalysisServiceError(
    RuntimeError
):
    """
    Raised when one of the scientific
    dependencies required by the complete
    GeneMirror analysis cannot execute.
    """


# ============================================================
# Prediction adapter
# ============================================================

def build_prediction_from_xai(
    xai_response,
) -> PredictionResult:

    result = (
        xai_response.result
    )

    explanation = (
        xai_response.explanation
    )

    return PredictionResult(
        predicted_class=(
            result.predicted_class
        ),
        predicted_class_name=(
            result.predicted_class_name
        ),
        raw_model_score=(
            result.raw_model_score
        ),
        calibrated_probability=(
            result.calibrated_probability
        ),
        confidence_score=(
            result.confidence_score
        ),
        uncertainty_score=(
            result.uncertainty_score
        ),
        confidence_band=(
            result.confidence_band
        ),
        impact_class=(
            result.impact_class
        ),
        model_name=(
            explanation.model_name
        ),
        model_version=(
            explanation.model_version
        ),
        target_interpretation=(
            explanation.target_interpretation
        ),

        # The standalone Sprint 4 prediction
        # endpoint contains the original raw-score
        # interpretation. The unified endpoint is
        # exposing the already-verified XAI result,
        # so no replacement interpretation is
        # invented here.
        score_interpretation=None,
    )


# ============================================================
# Cross-component consistency checks
# ============================================================

def verify_unified_consistency(
    *,
    request: VariantRequest,
    prediction: PredictionResult,
    xai_response,
    protein_response,
    scientist_response,
) -> None:

    # --------------------------------------------------------
    # Variant identity
    # --------------------------------------------------------

    expected_gene = (
        request.gene_symbol
    )

    if (
        xai_response.variant.gene_symbol
        != expected_gene
    ):

        raise UnifiedAnalysisServiceError(
            "XAI variant identity does not "
            "match the requested gene."
        )

    if (
        protein_response.variant.gene_symbol
        != expected_gene
    ):

        raise UnifiedAnalysisServiceError(
            "Protein-context variant identity "
            "does not match the requested gene."
        )

    if (
        scientist_response.variant.gene_symbol
        != expected_gene
    ):

        raise UnifiedAnalysisServiceError(
            "Scientist variant identity does not "
            "match the requested gene."
        )

    # --------------------------------------------------------
    # Prediction / XAI consistency
    # --------------------------------------------------------

    if (
        prediction.predicted_class
        != xai_response.result.predicted_class
    ):

        raise UnifiedAnalysisServiceError(
            "Prediction class is inconsistent "
            "with the XAI result."
        )

    if (
        prediction.predicted_class_name
        != xai_response
        .result
        .predicted_class_name
    ):

        raise UnifiedAnalysisServiceError(
            "Prediction class name is inconsistent "
            "with the XAI result."
        )

    if abs(
        prediction.raw_model_score
        - xai_response
        .result
        .raw_model_score
    ) > 1e-12:

        raise UnifiedAnalysisServiceError(
            "Raw model score is inconsistent "
            "between prediction and XAI."
        )

    if abs(
        prediction.calibrated_probability
        - xai_response
        .result
        .calibrated_probability
    ) > 1e-12:

        raise UnifiedAnalysisServiceError(
            "Calibrated probability is "
            "inconsistent between prediction "
            "and XAI."
        )

    if (
        prediction.impact_class
        != xai_response
        .result
        .impact_class
    ):

        raise UnifiedAnalysisServiceError(
            "Impact class is inconsistent "
            "between prediction and XAI."
        )

    # --------------------------------------------------------
    # Protein identity consistency
    # --------------------------------------------------------

    if (
        protein_response
        .protein
        .gene_symbol
        != expected_gene
    ):

        raise UnifiedAnalysisServiceError(
            "Protein gene identity does not "
            "match the requested gene."
        )

    if (
        protein_response
        .sequence_context
        .protein_position
        != request.protein_position
    ):

        raise UnifiedAnalysisServiceError(
            "Protein position does not match "
            "the requested variant."
        )

    if not (
        protein_response
        .sequence_context
        .position_matches_reference
    ):

        raise UnifiedAnalysisServiceError(
            "Protein reference residue was not "
            "validated against UniProt."
        )

    # --------------------------------------------------------
    # Scientist safety / execution consistency
    # --------------------------------------------------------

    if (
        scientist_response
        .research_only
        is not True
    ):

        raise UnifiedAnalysisServiceError(
            "Scientist response lost the "
            "research-only safety flag."
        )

    if (
        scientist_response
        .execution
        .used_llm_response
        and scientist_response
        .execution
        .fallback_used
    ):

        raise UnifiedAnalysisServiceError(
            "Scientist execution metadata "
            "is internally inconsistent."
        )

    # --------------------------------------------------------
    # Global research-only safety
    # --------------------------------------------------------

    if (
        xai_response.research_only
        is not True
    ):

        raise UnifiedAnalysisServiceError(
            "XAI response lost the "
            "research-only safety flag."
        )

    if (
        protein_response.research_only
        is not True
    ):

        raise UnifiedAnalysisServiceError(
            "Protein-context response lost the "
            "research-only safety flag."
        )


# ============================================================
# Main unified analysis service
# ============================================================

def analyze_variant(
    request: VariantRequest,
    provider_name: Optional[
        str
    ] = None,
) -> UnifiedAnalysisResponse:

    # --------------------------------------------------------
    # 1. Variant validation
    # --------------------------------------------------------

    try:

        validation = (
            validate_variant_request(
                request
            )
        )

    except VariantValidationServiceError as error:

        raise UnifiedAnalysisServiceError(
            "Variant-validation dependency "
            f"failed: {error}"
        ) from error

    # --------------------------------------------------------
    # 2. Prediction + XAI + calibration + confidence
    # --------------------------------------------------------

    try:

        xai_response = (
            analyze_variant_xai(
                request
            )
        )

    except XAIServiceError as error:

        raise UnifiedAnalysisServiceError(
            "XAI dependency failed: "
            f"{error}"
        ) from error

    prediction = (
        build_prediction_from_xai(
            xai_response
        )
    )

    # --------------------------------------------------------
    # 3. Protein context
    # --------------------------------------------------------

    try:

        protein_response = (
            analyze_protein_context(
                request
            )
        )

    except ProteinContextValidationError as error:

        raise UnifiedAnalysisValidationError(
            str(error)
        ) from error

    except ProteinContextServiceError as error:

        raise UnifiedAnalysisServiceError(
            "Protein-context dependency "
            f"failed: {error}"
        ) from error

    # --------------------------------------------------------
    # 4. GeneMirror Scientist
    # --------------------------------------------------------

    try:

        scientist_response = (
            analyze_variant_with_scientist(
                request=request,
                provider_name=(
                    provider_name
                ),
            )
        )

    except ScientistVariantValidationError as error:

        raise UnifiedAnalysisValidationError(
            str(error)
        ) from error

    except ScientistServiceError as error:

        raise UnifiedAnalysisServiceError(
            "Scientist dependency failed: "
            f"{error}"
        ) from error

    # --------------------------------------------------------
    # 5. Cross-component verification
    # --------------------------------------------------------

    verify_unified_consistency(
        request=request,
        prediction=prediction,
        xai_response=xai_response,
        protein_response=(
            protein_response
        ),
        scientist_response=(
            scientist_response
        ),
    )

    # --------------------------------------------------------
    # 6. API variant identity
    # --------------------------------------------------------

    variant_identity = (
        build_prediction_variant_identity(
            request
        )
    )

    # --------------------------------------------------------
    # 7. Unified response
    # --------------------------------------------------------

    return UnifiedAnalysisResponse(
        success=True,
        variant=variant_identity,
        validation=validation,
        prediction=prediction,
        xai=xai_response,
        protein_context=(
            protein_response
        ),
        scientist=(
            scientist_response
        ),
        research_only=True,
        disclaimer=(
            RESEARCH_DISCLAIMER
        ),
    )