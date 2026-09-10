import json
import math
import sys
from pathlib import Path
from typing import Any, Dict


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

from backend.explainability.calibration import (
    calibrate_probability,
)

from backend.explainability.config import (
    ARTIFACTS_DIR,
    CALIBRATION_VERSION,
    MODEL_NAME,
    MODEL_VERSION,
    TARGET_INTERPRETATION,
)

from backend.modeling.predictor import (
    predict_variant,
)


# ============================================================
# Configuration
# ============================================================

CONFIDENCE_VERSION = (
    "GeneMirror-Confidence-v1"
)

CONFIDENCE_EXAMPLE_PATH = (
    ARTIFACTS_DIR
    / "confidence_example_v1.json"
)

EPSILON = 1e-12


# ============================================================
# Probability validation
# ============================================================

def validate_probability(
    probability: float,
) -> float:

    try:

        probability = float(
            probability
        )

    except (
        TypeError,
        ValueError,
    ) as error:

        raise ValueError(
            "Probability must be numeric."
        ) from error

    if not math.isfinite(
        probability
    ):

        raise ValueError(
            "Probability must be finite."
        )

    if not (
        0.0
        <= probability
        <= 1.0
    ):

        raise ValueError(
            "Probability must be "
            "between 0 and 1."
        )

    return probability


# ============================================================
# Binary entropy
# ============================================================

def calculate_uncertainty(
    calibrated_probability: float,
) -> float:

    p = validate_probability(
        calibrated_probability
    )

    # Perfectly decisive predictions
    if (
        p <= EPSILON
        or p >= 1.0 - EPSILON
    ):

        return 0.0

    entropy = -(
        p * math.log2(
            p
        )
        + (
            1.0 - p
        )
        * math.log2(
            1.0 - p
        )
    )

    # Binary entropy is already normalized to [0, 1]
    uncertainty = float(
        entropy
    )

    return min(
        max(
            uncertainty,
            0.0,
        ),
        1.0,
    )


# ============================================================
# Decision confidence
# ============================================================

def calculate_confidence(
    calibrated_probability: float,
) -> float:

    uncertainty = (
        calculate_uncertainty(
            calibrated_probability
        )
    )

    confidence = (
        1.0
        - uncertainty
    )

    return min(
        max(
            float(
                confidence
            ),
            0.0,
        ),
        1.0,
    )


# ============================================================
# Confidence band
# ============================================================

def confidence_band(
    confidence_score: float,
) -> str:

    confidence_score = (
        validate_probability(
            confidence_score
        )
    )

    if confidence_score >= 0.70:

        return "HIGH"

    if confidence_score >= 0.35:

        return "MODERATE"

    return "LOW"


# ============================================================
# Build confidence result
# ============================================================

def build_confidence_result(
    raw_model_score: float,
) -> Dict[str, Any]:

    raw_model_score = (
        validate_probability(
            raw_model_score
        )
    )

    calibrated_probability = (
        calibrate_probability(
            raw_model_score
        )
    )

    uncertainty_score = (
        calculate_uncertainty(
            calibrated_probability
        )
    )

    confidence_score = (
        calculate_confidence(
            calibrated_probability
        )
    )

    result = {
        "raw_model_score": (
            raw_model_score
        ),

        "calibrated_probability": (
            calibrated_probability
        ),

        "uncertainty_score": (
            uncertainty_score
        ),

        "confidence_score": (
            confidence_score
        ),

        "confidence_band": (
            confidence_band(
                confidence_score
            )
        ),

        "confidence_method": (
            "one_minus_normalized_binary_entropy"
        ),

        "uncertainty_method": (
            "normalized_binary_entropy"
        ),

        "calibration_version": (
            CALIBRATION_VERSION
        ),

        "confidence_version": (
            CONFIDENCE_VERSION
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

        "probability_interpretation": (
            "Calibrated probability of the "
            "ClinVar-derived pathogenic-like "
            "proxy class."
        ),

        "confidence_interpretation": (
            "Decision confidence derived from "
            "how far the calibrated probability "
            "is from maximum uncertainty. "
            "It reflects prediction decisiveness, "
            "not biological certainty, epistemic "
            "uncertainty, or clinical confidence."
        ),

        "uncertainty_interpretation": (
            "Normalized binary entropy of the "
            "calibrated probability. Values near "
            "1 indicate greater decision uncertainty; "
            "values near 0 indicate a more decisive "
            "model output."
        ),

        "test_set_used": False,

        "research_only": True,
    }

    return result


# ============================================================
# Variant-level helper
# ============================================================

def evaluate_variant_confidence(
    variant: Dict[str, Any],
) -> Dict[str, Any]:

    prediction = predict_variant(
        variant
    )

    confidence_result = (
        build_confidence_result(
            prediction[
                "model_score"
            ]
        )
    )

    result = {
        "variant": {
            "reference_allele": (
                str(
                    variant[
                        "reference_allele"
                    ]
                )
                .strip()
                .upper()
            ),

            "alternate_allele": (
                str(
                    variant[
                        "alternate_allele"
                    ]
                )
                .strip()
                .upper()
            ),

            "reference_aa": (
                str(
                    variant[
                        "reference_aa"
                    ]
                )
                .strip()
                .upper()
            ),

            "alternate_aa": (
                str(
                    variant[
                        "alternate_aa"
                    ]
                )
                .strip()
                .upper()
            ),

            "protein_position": int(
                variant[
                    "protein_position"
                ]
            ),
        },

        "predicted_class": (
            prediction[
                "predicted_class"
            ]
        ),

        "predicted_class_name": (
            prediction[
                "predicted_class_name"
            ]
        ),

        **confidence_result,
    }

    return result


# ============================================================
# Verification
# ============================================================

def verify_confidence_result(
    result: Dict[str, Any],
) -> None:

    required_keys = {
        "raw_model_score",
        "calibrated_probability",
        "uncertainty_score",
        "confidence_score",
        "confidence_band",
        "test_set_used",
    }

    missing = (
        required_keys
        - set(
            result.keys()
        )
    )

    if missing:

        raise ValueError(
            "Confidence result missing "
            f"required keys: "
            f"{sorted(missing)}"
        )

    for field in [
        "raw_model_score",
        "calibrated_probability",
        "uncertainty_score",
        "confidence_score",
    ]:

        value = float(
            result[
                field
            ]
        )

        if not math.isfinite(
            value
        ):

            raise ValueError(
                f"{field} is not finite."
            )

        if not (
            0.0
            <= value
            <= 1.0
        ):

            raise ValueError(
                f"{field} is outside [0, 1]."
            )

    expected_sum = (
        result[
            "confidence_score"
        ]
        + result[
            "uncertainty_score"
        ]
    )

    if not math.isclose(
        expected_sum,
        1.0,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):

        raise ValueError(
            "Confidence and uncertainty "
            "must sum to 1."
        )

    if result[
        "confidence_band"
    ] not in {
        "LOW",
        "MODERATE",
        "HIGH",
    }:

        raise ValueError(
            "Invalid confidence band."
        )

    if result[
        "test_set_used"
    ] is not False:

        raise ValueError(
            "Test set must not be used "
            "for confidence calculation."
        )


# ============================================================
# Save artifact
# ============================================================

def save_confidence_example(
    result: Dict[str, Any],
) -> None:

    with open(
        CONFIDENCE_EXAMPLE_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            result,
            file,
            indent=2,
        )


# ============================================================
# Smoke test
# ============================================================

def main():

    print(
        "GeneMirror Sprint 5 "
        "Confidence & Uncertainty Engine"
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
        "\nGenerating frozen Sprint 4 "
        "prediction..."
    )

    result = (
        evaluate_variant_confidence(
            variant
        )
    )

    print(
        "Prediction generated."
    )

    print(
        "\nVerifying confidence result..."
    )

    verify_confidence_result(
        result
    )

    print(
        "Confidence result verified."
    )

    save_confidence_example(
        result
    )

    print(
        f"\nPredicted class: "
        f"{result['predicted_class_name']}"
    )

    print(
        f"Raw model score: "
        f"{result['raw_model_score']:.6f}"
    )

    print(
        f"Calibrated probability: "
        f"{result['calibrated_probability']:.6f}"
    )

    print(
        f"Uncertainty score: "
        f"{result['uncertainty_score']:.6f}"
    )

    print(
        f"Decision confidence: "
        f"{result['confidence_score']:.6f}"
    )

    print(
        f"Confidence band: "
        f"{result['confidence_band']}"
    )

    print(
        "\nTest set used:",
        result[
            "test_set_used"
        ],
    )

    print(
        "\nOutput:"
    )

    print(
        CONFIDENCE_EXAMPLE_PATH
    )

    print(
        "\nImportant:"
    )

    print(
        "Decision confidence measures "
        "probability decisiveness only."
    )

    print(
        "It is NOT biological certainty, "
        "clinical confidence, or "
        "epistemic uncertainty."
    )

    print(
        "\n✅ Sprint 5 confidence and "
        "uncertainty engine completed."
    )


if __name__ == "__main__":
    main()