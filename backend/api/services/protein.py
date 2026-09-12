from typing import (
    Any,
    Dict,
)


# ============================================================
# Frozen Sprint 6 engine
# ============================================================

from backend.protein_context.visualization_engine import (
    build_protein_visualization,
    verify_visualization_payload,
)

from backend.protein_context.variant_validator import (
    ProteinVariantValidationError,
)


# ============================================================
# API adapters
# ============================================================

from backend.api.services.prediction import (
    build_prediction_variant_identity,
)


# ============================================================
# API schemas
# ============================================================

from backend.api.schemas.variant import (
    VariantRequest,
)

from backend.api.schemas.protein import (
    ProteinContextResponse,
    ProteinFeatureResponse,
    ProteinIdentityResponse,
    ProteinSequenceContextResponse,
    ProteinVariantResponse,
    VariantMarkerResponse,
    VisualizationFeatureResponse,
    VisualizationTrackResponse,
)


# ============================================================
# Exceptions
# ============================================================

class ProteinContextValidationError(
    ValueError
):
    """
    Raised when the supplied protein variant
    fails scientific validation against the
    retrieved protein sequence.
    """


class ProteinContextServiceError(
    RuntimeError
):
    """
    Raised when the Sprint 6 protein-context
    engine or an upstream protein service
    cannot complete analysis.
    """


# ============================================================
# Protein identity adapter
# ============================================================

def build_protein_identity_response(
    protein,
) -> ProteinIdentityResponse:

    return ProteinIdentityResponse(
        accession=protein.accession,
        gene_symbol=protein.gene_symbol,
        protein_name=protein.protein_name,
        organism=protein.organism,
        sequence_length=(
            protein.sequence_length
        ),
        reviewed=protein.reviewed,
        entry_name=protein.entry_name,
        source=protein.source,
    )


# ============================================================
# Sequence-context adapter
# ============================================================

def build_sequence_context_response(
    context,
) -> ProteinSequenceContextResponse:

    return (
        ProteinSequenceContextResponse(
            protein_position=(
                context.protein_position
            ),
            reference_amino_acid=(
                context.reference_amino_acid
            ),
            sequence_reference_amino_acid=(
                context.sequence_reference_amino_acid
            ),
            position_matches_reference=(
                context.position_matches_reference
            ),
            window_start=(
                context.window_start
            ),
            window_end=(
                context.window_end
            ),
            sequence_window=(
                context.sequence_window
            ),
            variant_index_in_window=(
                context.variant_index_in_window
            ),
            protein_length=(
                context.protein_length
            ),
        )
    )


# ============================================================
# Protein-feature adapter
# ============================================================

def build_feature_response(
    feature,
) -> ProteinFeatureResponse:

    return ProteinFeatureResponse(
        feature_type=(
            feature.feature_type
        ),
        start=feature.start,
        end=feature.end,
        description=(
            feature.description
        ),
        feature_id=(
            feature.feature_id
        ),
        evidence=list(
            feature.evidence
        ),
        distance_to_variant=(
            feature.distance_to_variant
        ),
        overlaps_variant=(
            feature.overlaps_variant
        ),
    )


# ============================================================
# Visualization feature adapter
# ============================================================

def build_visualization_feature_response(
    feature: Dict[str, Any],
) -> VisualizationFeatureResponse:

    return (
        VisualizationFeatureResponse(
            feature_type=str(
                feature[
                    "feature_type"
                ]
            ),
            start=int(
                feature[
                    "start"
                ]
            ),
            end=int(
                feature[
                    "end"
                ]
            ),
            start_fraction=float(
                feature[
                    "start_fraction"
                ]
            ),
            end_fraction=float(
                feature[
                    "end_fraction"
                ]
            ),
            description=(
                feature.get(
                    "description"
                )
            ),
            feature_id=(
                feature.get(
                    "feature_id"
                )
            ),
            evidence=list(
                feature.get(
                    "evidence",
                    [],
                )
            ),
            overlaps_variant=bool(
                feature.get(
                    "overlaps_variant",
                    False,
                )
            ),
            distance_to_variant=(
                feature.get(
                    "distance_to_variant"
                )
            ),
        )
    )


# ============================================================
# Visualization-track adapter
# ============================================================

def build_visualization_track_response(
    track,
) -> VisualizationTrackResponse:

    return VisualizationTrackResponse(
        track_type=track.track_type,
        label=track.label,
        features=[
            build_visualization_feature_response(
                feature
            )
            for feature
            in track.features
        ],
    )


# ============================================================
# Variant marker adapter
# ============================================================

def build_variant_marker_response(
    marker,
):

    if marker is None:
        return None

    return VariantMarkerResponse(
        position=marker.position,
        reference_amino_acid=(
            marker.reference_amino_acid
        ),
        alternate_amino_acid=(
            marker.alternate_amino_acid
        ),
        label=marker.label,
    )


# ============================================================
# Protein-relative variant adapter
# ============================================================

def build_protein_variant_response(
    variant: Dict[str, Any],
) -> ProteinVariantResponse:

    return ProteinVariantResponse(
        gene_symbol=str(
            variant[
                "gene_symbol"
            ]
        ),
        protein_position=int(
            variant[
                "protein_position"
            ]
        ),
        reference_amino_acid=str(
            variant[
                "reference_aa"
            ]
        ),
        alternate_amino_acid=str(
            variant[
                "alternate_aa"
            ]
        ),
        amino_acid_change=str(
            variant[
                "amino_acid_change"
            ]
        ),
        normalized_position=float(
            variant[
                "normalized_position"
            ]
        ),
    )


# ============================================================
# Main service
# ============================================================

def analyze_protein_context(
    request: VariantRequest,
) -> ProteinContextResponse:

    variant_identity = (
        build_prediction_variant_identity(
            request
        )
    )

    try:

        result = (
            build_protein_visualization(
                gene_symbol=(
                    request.gene_symbol
                ),
                protein_position=(
                    request.protein_position
                ),
                reference_aa=(
                    request.reference_amino_acid
                ),
                alternate_aa=(
                    request.alternate_amino_acid
                ),
            )
        )

        # The frozen Sprint 6 engine already
        # validates its result internally.
        # This second explicit verification
        # protects the API boundary as well.

        verify_visualization_payload(
            result
        )

    except ProteinVariantValidationError as error:

        raise (
            ProteinContextValidationError(
                str(error)
            )
        ) from error

    except ValueError as error:

        raise (
            ProteinContextValidationError(
                str(error)
            )
        ) from error

    except Exception as error:

        raise ProteinContextServiceError(
            "Protein context analysis failed: "
            f"{error}"
        ) from error

    protein = (
        build_protein_identity_response(
            result.protein
        )
    )

    sequence_context = (
        build_sequence_context_response(
            result.sequence_context
        )
    )

    protein_variant = (
        build_protein_variant_response(
            result.variant
        )
    )

    overlapping_features = [
        build_feature_response(
            feature
        )
        for feature
        in result.overlapping_features
    ]

    nearby_features = [
        build_feature_response(
            feature
        )
        for feature
        in result.nearby_features
    ]

    visualization_tracks = [
        build_visualization_track_response(
            track
        )
        for track
        in result.visualization_tracks
    ]

    variant_marker = (
        build_variant_marker_response(
            result.variant_marker
        )
    )

    return ProteinContextResponse(
        success=True,
        variant=variant_identity,
        protein_variant=(
            protein_variant
        ),
        protein=protein,
        sequence_context=(
            sequence_context
        ),
        overlapping_features=(
            overlapping_features
        ),
        nearby_features=(
            nearby_features
        ),
        visualization_tracks=(
            visualization_tracks
        ),
        variant_marker=(
            variant_marker
        ),
        protein_context_version=(
            result.protein_context_version
        ),
        visualization_version=(
            result.visualization_version
        ),
        interpretation=(
            result.interpretation
        ),
        research_only=(
            result.research_only
        ),
        disclaimer=(
            result.disclaimer
        ),
    )