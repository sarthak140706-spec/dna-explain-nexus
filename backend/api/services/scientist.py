from typing import (
    Any,
    Dict,
    Optional,
)


# ============================================================
# Frozen Sprint 7 contracts
# ============================================================

from backend.scientist.contracts import (
    ScientistFeatureContribution,
    ScientistInput,
    ScientistPrediction,
    ScientistProteinContext,
    ScientistVariant,
)

from backend.scientist.scientist_engine import (
    run_gene_mirror_scientist,
    verify_scientist_result,
)


# ============================================================
# Existing Sprint 8 services
# ============================================================

from backend.api.services.xai import (
    XAIServiceError,
    analyze_variant_xai,
)

from backend.api.services.protein import (
    ProteinContextServiceError,
    ProteinContextValidationError,
    analyze_protein_context,
)


# ============================================================
# API schemas
# ============================================================

from backend.api.schemas.variant import (
    VariantRequest,
)

from backend.api.schemas.scientist import (
    ScientistExecutionMetadata,
    ScientistResponse,
    ScientistSectionsResponse,
)


# ============================================================
# Exceptions
# ============================================================

class ScientistServiceError(
    RuntimeError
):
    """
    Raised when the GeneMirror Scientist
    pipeline cannot complete.
    """


class ScientistVariantValidationError(
    ValueError
):
    """
    Raised when protein-level scientific
    validation fails for the supplied variant.
    """


# ============================================================
# Direction adapter
# ============================================================

def map_xai_direction(
    direction: str,
) -> str:

    mapping = {
        "supports_higher_impact": (
            "supports_higher"
        ),
        "supports_lower_impact": (
            "supports_lower"
        ),
        "neutral": "neutral",
    }

    if direction not in mapping:

        raise ScientistServiceError(
            "Unsupported XAI contribution "
            f"direction: {direction}"
        )

    return mapping[
        direction
    ]


# ============================================================
# Variant adapter
# ============================================================

def build_scientist_variant(
    request: VariantRequest,
) -> ScientistVariant:

    return ScientistVariant(
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
        dna_change=(
            request.dna_change
        ),
        protein_change=(
            request.protein_change
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
    )


# ============================================================
# Prediction adapter
# ============================================================

def build_scientist_prediction(
    xai_response,
) -> ScientistPrediction:

    result = (
        xai_response.result
    )

    explanation = (
        xai_response.explanation
    )

    return ScientistPrediction(
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
        impact_class=(
            result.impact_class
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
        model_name=(
            explanation.model_name
        ),
        model_version=(
            explanation.model_version
        ),
    )


# ============================================================
# Feature-contribution adapter
# ============================================================

def build_scientist_contributions(
    xai_response,
):

    contributions = []

    # Use the frozen Sprint 5 ranked local
    # explanation. Top features are sufficient
    # for the Scientist explanation layer.

    for feature in (
        xai_response
        .explanation
        .top_features
    ):

        direction = (
            map_xai_direction(
                str(
                    feature[
                        "direction"
                    ]
                )
            )
        )

        contributions.append(
            ScientistFeatureContribution(
                feature_name=str(
                    feature[
                        "feature_name"
                    ]
                ),
                feature_value=(
                    feature.get(
                        "feature_value"
                    )
                ),
                contribution=float(
                    feature[
                        "raw_contribution"
                    ]
                ),
                direction=direction,
                relative_local_influence_percent=float(
                    feature[
                        "normalized_percent"
                    ]
                ),
            )
        )

    return contributions


# ============================================================
# Protein-feature adapter
# ============================================================

def protein_feature_to_dict(
    feature,
) -> Dict[str, Any]:

    return {
        "feature_type": (
            feature.feature_type
        ),
        "start": feature.start,
        "end": feature.end,
        "description": (
            feature.description
        ),
        "feature_id": (
            feature.feature_id
        ),
        "evidence": list(
            feature.evidence
        ),
        "distance_to_variant": (
            feature.distance_to_variant
        ),
        "overlaps_variant": (
            feature.overlaps_variant
        ),
    }


# ============================================================
# Protein-context adapter
# ============================================================

def build_scientist_protein_context(
    protein_response,
) -> ScientistProteinContext:

    context = (
        protein_response
        .sequence_context
    )

    protein = (
        protein_response
        .protein
    )

    return ScientistProteinContext(
        accession=(
            protein.accession
        ),
        protein_name=(
            protein.protein_name
        ),
        protein_length=(
            protein.sequence_length
        ),
        sequence_window=(
            context.sequence_window
        ),
        window_start=(
            context.window_start
        ),
        window_end=(
            context.window_end
        ),
        overlapping_features=[
            protein_feature_to_dict(
                feature
            )
            for feature
            in protein_response
            .overlapping_features
        ],
        nearby_features=[
            protein_feature_to_dict(
                feature
            )
            for feature
            in protein_response
            .nearby_features
        ],
    )


# ============================================================
# Source-version metadata
# ============================================================

def build_source_versions(
    xai_response,
    protein_response,
) -> Dict[str, str]:

    versions: Dict[
        str,
        str
    ] = {}

    if (
        xai_response
        .explanation
        .model_version
    ):

        versions[
            "prediction_model"
        ] = (
            xai_response
            .explanation
            .model_version
        )

    if (
        xai_response
        .result
        .calibration_version
    ):

        versions[
            "calibration"
        ] = (
            xai_response
            .result
            .calibration_version
        )

    if (
        xai_response
        .explanation
        .explanation_version
    ):

        versions[
            "xai"
        ] = (
            xai_response
            .explanation
            .explanation_version
        )

    versions[
        "protein_context"
    ] = (
        protein_response
        .protein_context_version
    )

    versions[
        "protein_visualization"
    ] = (
        protein_response
        .visualization_version
    )

    return versions


# ============================================================
# Complete Scientist input
# ============================================================

def build_scientist_input(
    request: VariantRequest,
    xai_response,
    protein_response,
) -> ScientistInput:

    return ScientistInput(
        variant=(
            build_scientist_variant(
                request
            )
        ),
        prediction=(
            build_scientist_prediction(
                xai_response
            )
        ),
        feature_contributions=(
            build_scientist_contributions(
                xai_response
            )
        ),
        protein_context=(
            build_scientist_protein_context(
                protein_response
            )
        ),
        grounded_evidence=[],
        source_versions=(
            build_source_versions(
                xai_response,
                protein_response,
            )
        ),
        research_only=True,
    )


# ============================================================
# API variant identity
# ============================================================

def build_api_variant_identity(
    request: VariantRequest,
):

    from backend.api.services.prediction import (
        build_prediction_variant_identity,
    )

    return (
        build_prediction_variant_identity(
            request
        )
    )


# ============================================================
# Main Scientist API service
# ============================================================

def analyze_variant_with_scientist(
    request: VariantRequest,
    provider_name: Optional[
        str
    ] = None,
) -> ScientistResponse:

    # --------------------------------------------------------
    # Generate the frozen Sprint 5 prediction/XAI result.
    # --------------------------------------------------------

    try:

        xai_response = (
            analyze_variant_xai(
                request
            )
        )

    except XAIServiceError as error:

        raise ScientistServiceError(
            "Scientist XAI dependency failed: "
            f"{error}"
        ) from error

    # --------------------------------------------------------
    # Generate the frozen Sprint 6 protein context.
    # --------------------------------------------------------

    try:

        protein_response = (
            analyze_protein_context(
                request
            )
        )

    except ProteinContextValidationError as error:

        raise (
            ScientistVariantValidationError(
                str(error)
            )
        ) from error

    except ProteinContextServiceError as error:

        raise ScientistServiceError(
            "Scientist protein-context "
            f"dependency failed: {error}"
        ) from error

    # --------------------------------------------------------
    # Construct exact Sprint 7 input contract.
    # --------------------------------------------------------

    scientist_input = (
        build_scientist_input(
            request=request,
            xai_response=(
                xai_response
            ),
            protein_response=(
                protein_response
            ),
        )
    )

    # --------------------------------------------------------
    # Run frozen Sprint 7 Scientist.
    # --------------------------------------------------------

    try:

        result = (
            run_gene_mirror_scientist(
                scientist_input,
                provider_name=(
                    provider_name
                ),
            )
        )

        verify_scientist_result(
            result
        )

    except Exception as error:

        raise ScientistServiceError(
            "GeneMirror Scientist "
            f"execution failed: {error}"
        ) from error

    output = (
        result[
            "output"
        ]
    )

    metadata = (
        result[
            "metadata"
        ]
    )

    # --------------------------------------------------------
    # Adapt output to FastAPI schema.
    # --------------------------------------------------------

    sections = (
        ScientistSectionsResponse(
            overview=(
                output
                .sections
                .overview
            ),
            prediction=(
                output
                .sections
                .prediction
            ),
            evidence=(
                output
                .sections
                .evidence
            ),
            protein_context=(
                output
                .sections
                .protein_context
            ),
            limitations=(
                output
                .sections
                .limitations
            ),
        )
    )

    execution = (
        ScientistExecutionMetadata(
            requested_provider=(
                metadata[
                    "requested_provider"
                ]
            ),
            provider_used=(
                metadata[
                    "provider_used"
                ]
            ),
            used_llm_response=(
                metadata[
                    "used_llm_response"
                ]
            ),
            fallback_used=(
                metadata[
                    "fallback_used"
                ]
            ),
            fallback_reason=(
                metadata[
                    "fallback_reason"
                ]
            ),
            validation_errors=list(
                metadata[
                    "validation_errors"
                ]
            ),
        )
    )

    variant_identity = (
        build_api_variant_identity(
            request
        )
    )

    return ScientistResponse(
        success=True,
        variant=variant_identity,
        sections=sections,
        grounded_facts=list(
            output.grounded_facts
        ),
        scientist_name=(
            output.scientist_name
        ),
        scientist_version=(
            output.scientist_version
        ),
        contract_version=(
            output.contract_version
        ),

        # For deterministic fallback the
        # ScientistOutput provider itself can
        # remain None. The execution metadata
        # is the authoritative source for what
        # actually produced the response.
        provider=(
            metadata[
                "provider_used"
            ]
        ),

        language_model=(
            output.language_model
        ),
        execution=execution,
        research_only=(
            output.research_only
        ),
        disclaimer=(
            output.disclaimer
        ),
    )