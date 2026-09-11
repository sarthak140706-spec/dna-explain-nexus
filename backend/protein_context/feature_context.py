import sys
from dataclasses import replace
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

from backend.protein_context.contracts import (
    ProteinFeature,
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
# Feature distance
# ============================================================

def calculate_feature_distance(
    protein_position: int,
    feature_start: int,
    feature_end: int,
) -> int:

    if (
        feature_start
        <= protein_position
        <= feature_end
    ):
        return 0

    if protein_position < feature_start:
        return (
            feature_start
            - protein_position
        )

    return (
        protein_position
        - feature_end
    )


# ============================================================
# Feature classification
# ============================================================

def classify_features_for_variant(
    features: List[ProteinFeature],
    protein_position: int,
    nearby_radius: int = 15,
) -> Dict[str, List[ProteinFeature]]:

    if nearby_radius < 0:

        raise ValueError(
            "Nearby radius cannot be negative."
        )

    overlapping_features = []
    nearby_features = []

    for feature in features:

        distance = calculate_feature_distance(
            protein_position=protein_position,
            feature_start=feature.start,
            feature_end=feature.end,
        )

        overlaps = (
            distance == 0
        )

        updated_feature = replace(
            feature,
            distance_to_variant=distance,
            overlaps_variant=overlaps,
        )

        if overlaps:

            overlapping_features.append(
                updated_feature
            )

        elif distance <= nearby_radius:

            nearby_features.append(
                updated_feature
            )

    overlapping_features.sort(
        key=lambda item: (
            item.start,
            item.end,
            item.feature_type,
        )
    )

    nearby_features.sort(
        key=lambda item: (
            item.distance_to_variant,
            item.start,
            item.end,
            item.feature_type,
        )
    )

    return {
        "overlapping_features": (
            overlapping_features
        ),
        "nearby_features": (
            nearby_features
        ),
    }


# ============================================================
# Gene-level feature context
# ============================================================

def get_variant_feature_context(
    gene_symbol: str,
    protein_position: int,
    reference_aa: str,
    alternate_aa: str,
    nearby_radius: int = 15,
) -> Dict[str, Any]:

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

    identity = parsed[
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

    classified = (
        classify_features_for_variant(
            features=features,
            protein_position=validation[
                "protein_position"
            ],
            nearby_radius=nearby_radius,
        )
    )

    return {
        "protein": identity,
        "variant": {
            "gene_symbol": (
                identity.gene_symbol
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
        },
        "overlapping_features": (
            classified[
                "overlapping_features"
            ]
        ),
        "nearby_features": (
            classified[
                "nearby_features"
            ]
        ),
        "nearby_radius": (
            nearby_radius
        ),
        "source": "UniProtKB",
    }


# ============================================================
# Verification
# ============================================================

def verify_feature_context(
    result: Dict[str, Any],
) -> None:

    position = result[
        "variant"
    ][
        "protein_position"
    ]

    protein_length = result[
        "protein"
    ].sequence_length

    overlapping = result[
        "overlapping_features"
    ]

    nearby = result[
        "nearby_features"
    ]

    for feature in overlapping:

        if not (
            feature.start
            <= position
            <= feature.end
        ):

            raise ValueError(
                "Overlapping feature does "
                "not contain variant."
            )

        if (
            feature.distance_to_variant
            != 0
        ):

            raise ValueError(
                "Overlapping feature must "
                "have distance 0."
            )

        if (
            feature.overlaps_variant
            is not True
        ):

            raise ValueError(
                "Overlapping feature flag "
                "is incorrect."
            )

    for feature in nearby:

        if (
            feature.distance_to_variant
            is None
            or feature.distance_to_variant
            <= 0
        ):

            raise ValueError(
                "Nearby feature distance "
                "must be positive."
            )

        if (
            feature.overlaps_variant
            is not False
        ):

            raise ValueError(
                "Nearby feature cannot "
                "overlap variant."
            )

        if not (
            1
            <= feature.start
            <= feature.end
            <= protein_length
        ):

            raise ValueError(
                "Nearby feature coordinates "
                "are invalid."
            )


# ============================================================
# CLI smoke test
# ============================================================

def main():

    print(
        "GeneMirror Sprint 6 "
        "Functional Region & Residue Context"
    )

    print(
        "=" * 72
    )

    result = (
        get_variant_feature_context(
            gene_symbol="TP53",
            protein_position=248,
            reference_aa="R",
            alternate_aa="H",
            nearby_radius=15,
        )
    )

    verify_feature_context(
        result
    )

    protein = result[
        "protein"
    ]

    variant = result[
        "variant"
    ]

    print(
        f"\nGene: "
        f"{protein.gene_symbol}"
    )

    print(
        f"Accession: "
        f"{protein.accession}"
    )

    print(
        f"Variant: "
        f"{variant['amino_acid_change']}"
    )

    print(
        f"Overlapping features: "
        f"{len(result['overlapping_features'])}"
    )

    print(
        f"Nearby features: "
        f"{len(result['nearby_features'])}"
    )

    print(
        "\nOverlapping annotations"
    )

    print(
        "-" * 72
    )

    for feature in (
        result[
            "overlapping_features"
        ]
    ):

        print(
            f"{feature.feature_type:20} "
            f"{feature.start:4}-"
            f"{feature.end:<4} "
            f"distance={feature.distance_to_variant:<3} "
            f"{feature.description}"
        )

    print(
        "\nNearest annotations"
    )

    print(
        "-" * 72
    )

    for feature in (
        result[
            "nearby_features"
        ][
            :10
        ]
    ):

        print(
            f"{feature.feature_type:20} "
            f"{feature.start:4}-"
            f"{feature.end:<4} "
            f"distance={feature.distance_to_variant:<3} "
            f"{feature.description}"
        )

    print(
        "\n✅ Functional feature context "
        "completed."
    )


if __name__ == "__main__":
    main()