import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List


# ============================================================
# Make project root importable
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# Imports
# ============================================================

from backend.protein_context.config import (
    PROTEIN_CONTEXT_INTERPRETATION,
    PROTEIN_CONTEXT_VERSION,
    PROTEIN_VISUALIZATION_VERSION,
    RESEARCH_DISCLAIMER,
)

from backend.protein_context.contracts import (
    ProteinContextResult,
    VariantMarker,
    VisualizationTrack,
    validate_protein_context_contract,
)

from backend.protein_context.context_engine import (
    build_sequence_context,
)

from backend.protein_context.feature_context import (
    classify_features_for_variant,
)

from backend.protein_context.parser import (
    parse_uniprot_entry,
    verify_parsed_protein,
)

from backend.protein_context.uniprot_client import (
    get_reviewed_human_protein,
)

from backend.protein_context.variant_validator import (
    validate_variant_against_sequence,
)


# ============================================================
# Coordinate normalization
# ============================================================

def normalize_position(
    position: int,
    protein_length: int,
) -> float:

    if protein_length <= 0:

        raise ValueError(
            "Protein length must be positive."
        )

    if not (
        1
        <= position
        <= protein_length
    ):

        raise ValueError(
            "Position is outside "
            "protein boundaries."
        )

    return (
        position
        / protein_length
    )


# ============================================================
# Feature visualization payload
# ============================================================

def feature_to_visualization_dict(
    feature,
    protein_length: int,
) -> Dict[str, Any]:

    return {
        "feature_type": (
            feature.feature_type
        ),

        "start": (
            feature.start
        ),

        "end": (
            feature.end
        ),

        "start_fraction": (
            normalize_position(
                feature.start,
                protein_length,
            )
        ),

        "end_fraction": (
            normalize_position(
                feature.end,
                protein_length,
            )
        ),

        "description": (
            feature.description
        ),

        "feature_id": (
            feature.feature_id
        ),

        "evidence": (
            feature.evidence
        ),

        "overlaps_variant": (
            feature.overlaps_variant
        ),

        "distance_to_variant": (
            feature.distance_to_variant
        ),
    }


# ============================================================
# Build tracks
# ============================================================

def build_visualization_tracks(
    all_features,
    protein_length: int,
) -> List[VisualizationTrack]:

    grouped = {}

    for feature in all_features:

        grouped.setdefault(
            feature.feature_type,
            [],
        )

        grouped[
            feature.feature_type
        ].append(
            feature_to_visualization_dict(
                feature,
                protein_length,
            )
        )

    tracks = []

    for feature_type in sorted(
        grouped.keys()
    ):

        features = grouped[
            feature_type
        ]

        features.sort(
            key=lambda item: (
                item["start"],
                item["end"],
            )
        )

        tracks.append(
            VisualizationTrack(
                track_type=(
                    feature_type
                    .lower()
                    .replace(" ", "_")
                ),
                label=feature_type,
                features=features,
            )
        )

    return tracks


# ============================================================
# Complete protein visualization payload
# ============================================================

def build_protein_visualization(
    gene_symbol: str,
    protein_position: int,
    reference_aa: str,
    alternate_aa: str,
    sequence_window_radius: int = 10,
    nearby_feature_radius: int = 15,
) -> ProteinContextResult:

    result = (
        get_reviewed_human_protein(
            gene_symbol
        )
    )

    parsed = (
        parse_uniprot_entry(
            result[
                "entry"
            ]
        )
    )

    verify_parsed_protein(
        parsed
    )

    protein = parsed[
        "identity"
    ]

    sequence = parsed[
        "sequence"
    ]

    features = parsed[
        "features"
    ]

    validation = (
        validate_variant_against_sequence(
            sequence=sequence,
            protein_position=protein_position,
            reference_aa=reference_aa,
            alternate_aa=alternate_aa,
        )
    )

    sequence_context = (
        build_sequence_context(
            sequence=sequence,
            protein_position=protein_position,
            reference_aa=reference_aa,
            alternate_aa=alternate_aa,
            window_radius=(
                sequence_window_radius
            ),
        )
    )

    classified = (
        classify_features_for_variant(
            features=features,
            protein_position=(
                validation[
                    "protein_position"
                ]
            ),
            nearby_radius=(
                nearby_feature_radius
            ),
        )
    )

    # Rebuild all feature distances so every track feature
    # carries variant-relative metadata.
    classified_all = (
        classify_features_for_variant(
            features=features,
            protein_position=(
                validation[
                    "protein_position"
                ]
            ),
            nearby_radius=(
                protein.sequence_length
            ),
        )
    )

    all_context_features = (
        classified_all[
            "overlapping_features"
        ]
        +
        classified_all[
            "nearby_features"
        ]
    )

    visualization_tracks = (
        build_visualization_tracks(
            all_features=(
                all_context_features
            ),
            protein_length=(
                protein.sequence_length
            ),
        )
    )

    variant_marker = (
        VariantMarker(
            position=(
                validation[
                    "protein_position"
                ]
            ),
            reference_amino_acid=(
                validation[
                    "reference_amino_acid"
                ]
            ),
            alternate_amino_acid=(
                validation[
                    "alternate_amino_acid"
                ]
            ),
            label=(
                validation[
                    "amino_acid_change"
                ]
            ),
        )
    )

    context_result = (
        ProteinContextResult(
            protein=protein,

            variant={
                "gene_symbol": (
                    protein.gene_symbol
                ),

                "protein_position": (
                    validation[
                        "protein_position"
                    ]
                ),

                "reference_aa": (
                    validation[
                        "reference_amino_acid"
                    ]
                ),

                "alternate_aa": (
                    validation[
                        "alternate_amino_acid"
                    ]
                ),

                "amino_acid_change": (
                    validation[
                        "amino_acid_change"
                    ]
                ),

                "normalized_position": (
                    normalize_position(
                        validation[
                            "protein_position"
                        ],
                        protein.sequence_length,
                    )
                ),
            },

            sequence_context=(
                sequence_context
            ),

            overlapping_features=(
                classified[
                    "overlapping_features"
                ]
            ),

            nearby_features=(
                classified[
                    "nearby_features"
                ]
            ),

            visualization_tracks=(
                visualization_tracks
            ),

            variant_marker=(
                variant_marker
            ),

            protein_context_version=(
                PROTEIN_CONTEXT_VERSION
            ),

            visualization_version=(
                PROTEIN_VISUALIZATION_VERSION
            ),

            interpretation=(
                PROTEIN_CONTEXT_INTERPRETATION
            ),

            research_only=True,

            disclaimer=(
                RESEARCH_DISCLAIMER
            ),
        )
    )

    validate_protein_context_contract(
        context_result
    )

    return context_result


# ============================================================
# Visualization verification
# ============================================================

def verify_visualization_payload(
    result: ProteinContextResult,
) -> None:

    validate_protein_context_contract(
        result
    )

    protein_length = (
        result.protein.sequence_length
    )

    marker = (
        result.variant_marker
    )

    if marker is None:

        raise ValueError(
            "Variant marker is missing."
        )

    if not (
        1
        <= marker.position
        <= protein_length
    ):

        raise ValueError(
            "Variant marker is outside "
            "protein boundaries."
        )

    normalized_position = (
        result.variant[
            "normalized_position"
        ]
    )

    if not (
        0.0
        < normalized_position
        <= 1.0
    ):

        raise ValueError(
            "Normalized variant position "
            "is invalid."
        )

    for track in (
        result.visualization_tracks
    ):

        if not track.label:

            raise ValueError(
                "Visualization track "
                "has no label."
            )

        for feature in track.features:

            if not (
                0.0
                < feature[
                    "start_fraction"
                ]
                <= 1.0
            ):

                raise ValueError(
                    "Feature start fraction "
                    "is invalid."
                )

            if not (
                0.0
                < feature[
                    "end_fraction"
                ]
                <= 1.0
            ):

                raise ValueError(
                    "Feature end fraction "
                    "is invalid."
                )

            if (
                feature[
                    "start_fraction"
                ]
                >
                feature[
                    "end_fraction"
                ]
            ):

                raise ValueError(
                    "Feature normalized "
                    "coordinates are invalid."
                )


# ============================================================
# CLI smoke test
# ============================================================

def main():

    print(
        "GeneMirror Sprint 6 "
        "Visualization Data Engine"
    )

    print(
        "=" * 72
    )

    result = (
        build_protein_visualization(
            gene_symbol="TP53",
            protein_position=248,
            reference_aa="R",
            alternate_aa="H",
        )
    )

    verify_visualization_payload(
        result
    )

    print(
        f"\nGene: "
        f"{result.protein.gene_symbol}"
    )

    print(
        f"Protein: "
        f"{result.protein.protein_name}"
    )

    print(
        f"Accession: "
        f"{result.protein.accession}"
    )

    print(
        f"Protein length: "
        f"{result.protein.sequence_length}"
    )

    print(
        f"Variant: "
        f"{result.variant_marker.label}"
    )

    print(
        "Normalized position:",
        round(
            result.variant[
                "normalized_position"
            ],
            6,
        ),
    )

    print(
        f"Overlapping features: "
        f"{len(result.overlapping_features)}"
    )

    print(
        f"Nearby features: "
        f"{len(result.nearby_features)}"
    )

    print(
        f"Visualization tracks: "
        f"{len(result.visualization_tracks)}"
    )

    print(
        "\nTracks"
    )

    print(
        "-" * 72
    )

    for track in (
        result.visualization_tracks
    ):

        print(
            f"{track.label:22} "
            f"{len(track.features)} features"
        )

    print(
        "\nSequence context:"
    )

    context = (
        result.sequence_context
    )

    print(
        f"{context.window_start}-"
        f"{context.window_end}: "
        f"{context.sequence_window}"
    )

    print(
        "\nResearch only:",
        result.research_only,
    )

    print(
        "\n✅ Visualization payload "
        "verification completed."
    )


if __name__ == "__main__":
    main()