import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List


# ============================================================
# Make project root importable for direct script execution
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

from backend.explainability.config import (
    ARTIFACTS_DIR,
    EXPLANATION_VERSION,
    MODEL_NAME,
    MODEL_VERSION,
    TARGET_INTERPRETATION,
)

from backend.explainability.local_explainer import (
    explain_variant,
)


# ============================================================
# Configuration
# ============================================================

NORMALIZATION_VERSION = (
    "GeneMirror-XAI-Normalization-v1"
)

NORMALIZED_EXPLANATION_PATH = (
    ARTIFACTS_DIR
    / "normalized_local_explanation_v1.json"
)

ZERO_TOLERANCE = 1e-12

TOP_FEATURE_COUNT = 10


# ============================================================
# Validation helpers
# ============================================================

def validate_raw_contributions(
    contributions: List[Any],
) -> None:

    if not contributions:

        raise ValueError(
            "No feature contributions were supplied."
        )

    feature_names = []

    for item in contributions:

        feature_name = (
            item.feature_name
        )

        contribution = float(
            item.contribution
        )

        direction = (
            item.direction
        )

        if not feature_name:

            raise ValueError(
                "Feature contribution contains "
                "an empty feature name."
            )

        if not math.isfinite(
            contribution
        ):

            raise ValueError(
                f"Non-finite contribution found "
                f"for feature: {feature_name}"
            )

        if direction not in {
            "supports_higher_impact",
            "supports_lower_impact",
            "neutral",
        }:

            raise ValueError(
                f"Invalid direction for "
                f"{feature_name}: {direction}"
            )

        feature_names.append(
            feature_name
        )

    if len(
        feature_names
    ) != len(
        set(feature_names)
    ):

        raise ValueError(
            "Duplicate feature names found "
            "in local contributions."
        )


# ============================================================
# Normalize local contributions
# ============================================================

def normalize_contributions(
    contributions: List[Any],
) -> List[Dict[str, Any]]:

    validate_raw_contributions(
        contributions
    )

    total_absolute_contribution = sum(
        abs(
            float(
                item.contribution
            )
        )
        for item in contributions
    )

    normalized = []

    for item in contributions:

        raw_contribution = float(
            item.contribution
        )

        absolute_contribution = abs(
            raw_contribution
        )

        if (
            total_absolute_contribution
            <= ZERO_TOLERANCE
        ):

            normalized_share = 0.0

        else:

            normalized_share = (
                absolute_contribution
                / total_absolute_contribution
            )

        normalized_percent = (
            normalized_share
            * 100.0
        )

        if raw_contribution > ZERO_TOLERANCE:

            signed_normalized_percent = (
                normalized_percent
            )

        elif raw_contribution < -ZERO_TOLERANCE:

            signed_normalized_percent = (
                -normalized_percent
            )

        else:

            signed_normalized_percent = 0.0

        normalized.append(
            {
                "feature_name": (
                    item.feature_name
                ),
                "feature_value": (
                    item.feature_value
                ),
                "raw_contribution": (
                    raw_contribution
                ),
                "absolute_contribution": (
                    absolute_contribution
                ),
                "normalized_share": (
                    normalized_share
                ),
                "normalized_percent": (
                    normalized_percent
                ),
                "signed_normalized_percent": (
                    signed_normalized_percent
                ),
                "direction": (
                    item.direction
                ),
            }
        )

    normalized.sort(
        key=lambda row: (
            row[
                "absolute_contribution"
            ]
        ),
        reverse=True,
    )

    for rank, row in enumerate(
        normalized,
        start=1,
    ):

        row[
            "rank"
        ] = rank

    return normalized


# ============================================================
# Summary statistics
# ============================================================

def calculate_direction_summary(
    normalized_contributions:
    List[Dict[str, Any]],
) -> Dict[str, float]:

    supporting = sum(
        row[
            "normalized_percent"
        ]
        for row
        in normalized_contributions
        if row[
            "direction"
        ]
        ==
        "supports_higher_impact"
    )

    opposing = sum(
        row[
            "normalized_percent"
        ]
        for row
        in normalized_contributions
        if row[
            "direction"
        ]
        ==
        "supports_lower_impact"
    )

    neutral = sum(
        row[
            "normalized_percent"
        ]
        for row
        in normalized_contributions
        if row[
            "direction"
        ]
        ==
        "neutral"
    )

    return {
        "supporting_higher_impact_percent": (
            supporting
        ),
        "supporting_lower_impact_percent": (
            opposing
        ),
        "neutral_percent": (
            neutral
        ),
        "total_percent": (
            supporting
            + opposing
            + neutral
        ),
    }


# ============================================================
# Build normalized explanation payload
# ============================================================

def build_normalized_explanation(
    variant: Dict[str, Any],
) -> Dict[str, Any]:

    explanation = explain_variant(
        variant
    )

    normalized = normalize_contributions(
        explanation.feature_contributions
    )

    direction_summary = (
        calculate_direction_summary(
            normalized
        )
    )

    total_absolute_contribution = sum(
        row[
            "absolute_contribution"
        ]
        for row in normalized
    )

    top_features = normalized[
        :TOP_FEATURE_COUNT
    ]

    payload = {
        "artifact_type": (
            "normalized_local_explanation"
        ),

        "normalization_version": (
            NORMALIZATION_VERSION
        ),

        "explanation_version": (
            EXPLANATION_VERSION
        ),

        "model_name": (
            MODEL_NAME
        ),

        "model_version": (
            MODEL_VERSION
        ),

        "target_interpretation": (
            TARGET_INTERPRETATION
        ),

        "variant": (
            explanation.variant
        ),

        "predicted_class": (
            explanation.predicted_class
        ),

        "predicted_class_name": (
            explanation.predicted_class_name
        ),

        "raw_model_score": (
            explanation.raw_model_score
        ),

        "normalization_method": (
            "absolute local perturbation magnitude"
        ),

        "normalization_formula": (
            "abs(feature_contribution) / "
            "sum(abs(all_feature_contributions))"
        ),

        "total_absolute_contribution": (
            total_absolute_contribution
        ),

        "feature_count": (
            len(normalized)
        ),

        "feature_contributions": (
            normalized
        ),

        "top_features": (
            top_features
        ),

        "direction_summary": (
            direction_summary
        ),

        "test_set_used": False,

        "percentage_interpretation": (
            "Normalized percentage represents "
            "the feature's share of the total "
            "absolute local perturbation magnitude. "
            "It is not the percentage of the model "
            "prediction and must not be interpreted "
            "as causal biological importance."
        ),

        "research_only": True,
    }

    return payload


# ============================================================
# Verify normalized explanation
# ============================================================

def verify_normalized_explanation(
    payload: Dict[str, Any],
) -> None:

    contributions = payload[
        "feature_contributions"
    ]

    if len(
        contributions
    ) != 28:

        raise ValueError(
            "Expected 28 normalized "
            f"features, found "
            f"{len(contributions)}."
        )

    normalized_total = sum(
        row[
            "normalized_percent"
        ]
        for row in contributions
    )

    total_absolute = payload[
        "total_absolute_contribution"
    ]

    if total_absolute > ZERO_TOLERANCE:

        if not math.isclose(
            normalized_total,
            100.0,
            rel_tol=1e-9,
            abs_tol=1e-8,
        ):

            raise ValueError(
                "Normalized percentages "
                "do not sum to 100."
            )

    for row in contributions:

        percent = row[
            "normalized_percent"
        ]

        share = row[
            "normalized_share"
        ]

        if not (
            0.0
            <= percent
            <= 100.0
        ):

            raise ValueError(
                "Normalized percentage "
                "outside [0, 100]."
            )

        if not (
            0.0
            <= share
            <= 1.0
        ):

            raise ValueError(
                "Normalized share "
                "outside [0, 1]."
            )

        raw = row[
            "raw_contribution"
        ]

        signed = row[
            "signed_normalized_percent"
        ]

        if (
            raw > ZERO_TOLERANCE
            and signed < 0
        ):

            raise ValueError(
                "Positive contribution received "
                "a negative normalized direction."
            )

        if (
            raw < -ZERO_TOLERANCE
            and signed > 0
        ):

            raise ValueError(
                "Negative contribution received "
                "a positive normalized direction."
            )

    direction_total = payload[
        "direction_summary"
    ][
        "total_percent"
    ]

    if total_absolute > ZERO_TOLERANCE:

        if not math.isclose(
            direction_total,
            100.0,
            rel_tol=1e-9,
            abs_tol=1e-8,
        ):

            raise ValueError(
                "Direction percentages "
                "do not sum to 100."
            )

    if payload[
        "test_set_used"
    ] is not False:

        raise ValueError(
            "Test set must not be used "
            "during Sprint 5 normalization."
        )


# ============================================================
# Save artifact
# ============================================================

def save_normalized_explanation(
    payload: Dict[str, Any],
) -> None:

    with open(
        NORMALIZED_EXPLANATION_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )


# ============================================================
# Smoke test
# ============================================================

def main():

    print(
        "GeneMirror Sprint 5 "
        "Feature Contribution Normalization"
    )

    print(
        "=" * 72
    )

    variant = {
        "reference_allele": "G",
        "alternate_allele": "A",
        "reference_aa": "R",
        "alternate_aa": "H",
        "protein_position": 248,
    }

    print(
        "\nGenerating local explanation..."
    )

    payload = (
        build_normalized_explanation(
            variant
        )
    )

    print(
        "Local explanation generated."
    )

    print(
        "\nVerifying normalization..."
    )

    verify_normalized_explanation(
        payload
    )

    print(
        "Normalization verified."
    )

    save_normalized_explanation(
        payload
    )

    print(
        f"\nPredicted class: "
        f"{payload['predicted_class_name']}"
    )

    print(
        f"Raw model score: "
        f"{payload['raw_model_score']:.6f}"
    )

    print(
        f"Feature count: "
        f"{payload['feature_count']}"
    )

    print(
        f"Total absolute contribution: "
        f"{payload['total_absolute_contribution']:.6f}"
    )

    print(
        "\nTop 10 normalized "
        "local contributions"
    )

    print(
        "-" * 100
    )

    print(
        f"{'Rank':<6}"
        f"{'Feature':<32}"
        f"{'Raw':>12}"
        f"{'Share %':>12} "
        f"{'Direction'}"
    )

    print(
        "-" * 100
    )

    for row in payload[
        "top_features"
    ]:

        print(
            f"{row['rank']:<6}"
            f"{row['feature_name']:<32}"
            f"{row['raw_contribution']:>12.6f}"
            f"{row['normalized_percent']:>12.2f} "
            f"{row['direction']}"
        )

    summary = payload[
        "direction_summary"
    ]

    print(
        "\nDirection summary"
    )

    print(
        "-" * 72
    )

    print(
        "Supports higher impact: "
        f"{summary['supporting_higher_impact_percent']:.2f}%"
    )

    print(
        "Supports lower impact:  "
        f"{summary['supporting_lower_impact_percent']:.2f}%"
    )

    print(
        "Neutral:                "
        f"{summary['neutral_percent']:.2f}%"
    )

    print(
        "Total:                  "
        f"{summary['total_percent']:.2f}%"
    )

    print(
        "\nTest set used:",
        payload[
            "test_set_used"
        ],
    )

    print(
        "\nOutput:"
    )

    print(
        NORMALIZED_EXPLANATION_PATH
    )

    print(
        "\nImportant:"
    )

    print(
        "Normalized percentages describe "
        "relative local perturbation magnitude."
    )

    print(
        "They are NOT percentages of the "
        "prediction and NOT causal "
        "biological importance."
    )

    print(
        "\n✅ Sprint 5 feature contribution "
        "normalization completed."
    )


if __name__ == "__main__":
    main()