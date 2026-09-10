import json
import math
import sys
from pathlib import Path
from typing import Any


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

from backend.explainability.calibration import (
    CALIBRATION_REPORT_PATH,
    CALIBRATOR_PATH,
    calibrate_probability,
)

from backend.explainability.confidence import (
    CONFIDENCE_EXAMPLE_PATH,
    calculate_confidence,
    calculate_uncertainty,
    evaluate_variant_confidence,
)

from backend.explainability.config import (
    ARTIFACTS_DIR,
    MODEL_ARTIFACT_PATH,
)

from backend.explainability.impact_mapper import (
    IMPACT_MAPPING_PATH,
    evaluate_variant_impact,
    load_impact_mapping,
    map_probability_to_impact,
)

from backend.modeling.predictor import (
    predict_variant,
)


# ============================================================
# Sprint 5 artifact paths
# ============================================================

GLOBAL_XAI_PATH = (
    ARTIFACTS_DIR
    / "global_feature_importance_v1.json"
)

LOCAL_XAI_PATH = (
    ARTIFACTS_DIR
    / "local_explanation_example_v1.json"
)

NORMALIZED_XAI_PATH = (
    ARTIFACTS_DIR
    / "normalized_local_explanation_v1.json"
)


# ============================================================
# Verification state
# ============================================================

PASSED = 0
FAILED = 0
FAILURES = []


# ============================================================
# Check helper
# ============================================================

def check(
    condition: bool,
    description: str,
) -> None:

    global PASSED
    global FAILED

    if condition:

        PASSED += 1

        print(
            f"✅ PASS | {description}"
        )

    else:

        FAILED += 1

        FAILURES.append(
            description
        )

        print(
            f"❌ FAIL | {description}"
        )


# ============================================================
# Exception helper
# ============================================================

def check_raises(
    function,
    description,
) -> None:

    try:

        function()

    except Exception:

        check(
            True,
            description,
        )

        return

    check(
        False,
        description,
    )


# ============================================================
# JSON loader
# ============================================================

def load_json(
    path: Path,
):

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(
            file
        )


# ============================================================
# Recursive JSON helpers
# ============================================================

def recursively_find_lists(
    value: Any,
):

    found = []

    if isinstance(
        value,
        list,
    ):

        found.append(
            value
        )

        for item in value:

            found.extend(
                recursively_find_lists(
                    item
                )
            )

    elif isinstance(
        value,
        dict,
    ):

        for item in value.values():

            found.extend(
                recursively_find_lists(
                    item
                )
            )

    return found


def find_feature_contribution_list(
    artifact,
):

    lists = recursively_find_lists(
        artifact
    )

    for values in lists:

        if not values:

            continue

        if not all(
            isinstance(
                row,
                dict,
            )
            for row in values
        ):

            continue

        first = values[
            0
        ]

        if (
            "feature_name"
            in first
            and "contribution"
            in first
        ):

            return values

    return None


def find_normalized_feature_list(
    artifact,
):

    lists = recursively_find_lists(
        artifact
    )

    for values in lists:

        if not values:

            continue

        if not all(
            isinstance(
                row,
                dict,
            )
            for row in values
        ):

            continue

        first = values[
            0
        ]

        if (
            "feature_name"
            not in first
        ):

            continue

        normalized_keys = {
            "normalized_percent",
            "signed_normalized_percent",
            "normalized_share",
        }

        if normalized_keys.intersection(
            first.keys()
        ):

            return values

    return None


def recursive_values_for_key(
    value,
    target_key,
):

    results = []

    if isinstance(
        value,
        dict,
    ):

        for key, item in value.items():

            if key == target_key:

                results.append(
                    item
                )

            results.extend(
                recursive_values_for_key(
                    item,
                    target_key,
                )
            )

    elif isinstance(
        value,
        list,
    ):

        for item in value:

            results.extend(
                recursive_values_for_key(
                    item,
                    target_key,
                )
            )

    return results


# ============================================================
# Main verification
# ============================================================

def main():

    global PASSED
    global FAILED

    print(
        "GeneMirror Sprint 5 "
        "Final Verification"
    )

    print(
        "=" * 78
    )

    # ========================================================
    # Section 1 — Artifact existence
    # ========================================================

    print(
        "\n[1] Artifact existence"
    )

    print(
        "-" * 78
    )

    check(
        MODEL_ARTIFACT_PATH.exists(),
        "Frozen Sprint 4 model artifact exists",
    )

    check(
        GLOBAL_XAI_PATH.exists(),
        "Global XAI artifact exists",
    )

    check(
        LOCAL_XAI_PATH.exists(),
        "Local XAI artifact exists",
    )

    check(
        NORMALIZED_XAI_PATH.exists(),
        "Normalized local XAI artifact exists",
    )

    check(
        CALIBRATOR_PATH.exists(),
        "Probability calibrator artifact exists",
    )

    check(
        CALIBRATION_REPORT_PATH.exists(),
        "Calibration report exists",
    )

    check(
        CONFIDENCE_EXAMPLE_PATH.exists(),
        "Confidence example artifact exists",
    )

    check(
        IMPACT_MAPPING_PATH.exists(),
        "Impact mapping artifact exists",
    )

    # Stop cleanly if fundamental files are unavailable.
    required_paths = [
        MODEL_ARTIFACT_PATH,
        GLOBAL_XAI_PATH,
        LOCAL_XAI_PATH,
        NORMALIZED_XAI_PATH,
        CALIBRATOR_PATH,
        CALIBRATION_REPORT_PATH,
        CONFIDENCE_EXAMPLE_PATH,
        IMPACT_MAPPING_PATH,
    ]

    if not all(
        path.exists()
        for path in required_paths
    ):

        print(
            "\nCannot continue because one "
            "or more Sprint 5 artifacts "
            "are missing."
        )

        final_summary()

        return

    # ========================================================
    # Load artifacts
    # ========================================================

    global_artifact = load_json(
        GLOBAL_XAI_PATH
    )

    local_artifact = load_json(
        LOCAL_XAI_PATH
    )

    normalized_artifact = load_json(
        NORMALIZED_XAI_PATH
    )

    calibration_report = load_json(
        CALIBRATION_REPORT_PATH
    )

    confidence_artifact = load_json(
        CONFIDENCE_EXAMPLE_PATH
    )

    impact_mapping = load_json(
        IMPACT_MAPPING_PATH
    )

    # ========================================================
    # Section 2 — Global XAI
    # ========================================================

    print(
        "\n[2] Global explainability"
    )

    print(
        "-" * 78
    )

    test_flags = recursive_values_for_key(
        global_artifact,
        "test_set_used",
    )

    check(
        (
            not test_flags
            or all(
                flag is False
                for flag in test_flags
            )
        ),
        "Global XAI does not indicate test-set usage",
    )

    feature_counts = recursive_values_for_key(
        global_artifact,
        "feature_count",
    )

    if feature_counts:

        check(
            any(
                int(
                    value
                )
                == 28
                for value in feature_counts
            ),
            "Global XAI contains 28 model features",
        )

    else:

        # Artifact schema may store only the feature table.
        lists = recursively_find_lists(
            global_artifact
        )

        feature_like_lists = []

        for values in lists:

            if (
                values
                and isinstance(
                    values[
                        0
                    ],
                    dict,
                )
            ):

                keys = set(
                    values[
                        0
                    ].keys()
                )

                if (
                    "feature_name"
                    in keys
                    or "feature"
                    in keys
                ):

                    feature_like_lists.append(
                        values
                    )

        check(
            any(
                len(
                    values
                )
                == 28
                for values in feature_like_lists
            ),
            "Global XAI contains 28 model features",
        )

    # ========================================================
    # Section 3 — Local XAI
    # ========================================================

    print(
        "\n[3] Local explainability"
    )

    print(
        "-" * 78
    )

    local_contributions = (
        find_feature_contribution_list(
            local_artifact
        )
    )

    check(
        local_contributions
        is not None,
        "Local XAI contribution list found",
    )

    if local_contributions is not None:

        check(
            len(
                local_contributions
            )
            == 28,
            "Local XAI contains 28 feature contributions",
        )

        valid_directions = {
            "supports_higher_impact",
            "supports_lower_impact",
            "neutral",
        }

        check(
            all(
                row.get(
                    "direction"
                )
                in valid_directions
                for row
                in local_contributions
            ),
            "Local XAI directions are valid",
        )

        check(
            all(
                math.isfinite(
                    float(
                        row[
                            "contribution"
                        ]
                    )
                )
                for row
                in local_contributions
            ),
            "Local XAI contributions are finite",
        )

    local_test_flags = (
        recursive_values_for_key(
            local_artifact,
            "test_set_used",
        )
    )

    check(
        (
            not local_test_flags
            or all(
                value is False
                for value
                in local_test_flags
            )
        ),
        "Local XAI does not indicate test-set usage",
    )

    # ========================================================
    # Section 4 — Normalized XAI
    # ========================================================

    print(
        "\n[4] Normalized local influence"
    )

    print(
        "-" * 78
    )

    normalized_features = (
        find_normalized_feature_list(
            normalized_artifact
        )
    )

    check(
        normalized_features
        is not None,
        "Normalized feature list found",
    )

    if normalized_features is not None:

        check(
            len(
                normalized_features
            )
            == 28,
            "Normalized explanation contains 28 features",
        )

        normalized_percent_values = []

        for row in normalized_features:

            if (
                "normalized_percent"
                in row
            ):

                normalized_percent_values.append(
                    float(
                        row[
                            "normalized_percent"
                        ]
                    )
                )

            elif (
                "normalized_share"
                in row
            ):

                normalized_percent_values.append(
                    float(
                        row[
                            "normalized_share"
                        ]
                    )
                    * 100.0
                )

        check(
            len(
                normalized_percent_values
            )
            == 28,
            "Normalized percentage/share available for all features",
        )

        if normalized_percent_values:

            normalized_total = sum(
                normalized_percent_values
            )

            check(
                math.isclose(
                    normalized_total,
                    100.0,
                    rel_tol=1e-8,
                    abs_tol=1e-8,
                ),
                "Normalized local influence totals 100%",
            )

            check(
                all(
                    value >= 0.0
                    for value
                    in normalized_percent_values
                ),
                "Normalized influence magnitudes are non-negative",
            )

    # ========================================================
    # Section 5 — Calibration
    # ========================================================

    print(
        "\n[5] Probability calibration"
    )

    print(
        "-" * 78
    )

    check(
        calibration_report.get(
            "selected_method"
        )
        == "isotonic",
        "Frozen calibration method is isotonic",
    )

    check(
        calibration_report.get(
            "test_set_used"
        )
        is False,
        "Calibration did not use the test set",
    )

    check(
        calibration_report.get(
            "validation_rows"
        )
        == 29640,
        "Calibration validation row count is 29,640",
    )

    check(
        calibration_report.get(
            "validation_genes"
        )
        == 2361,
        "Calibration validation gene count is 2,361",
    )

    folds = calibration_report.get(
        "cv_folds",
        [],
    )

    check(
        len(
            folds
        )
        == 5,
        "Calibration contains five grouped CV folds",
    )

    check(
        all(
            fold.get(
                "gene_overlap"
            )
            == 0
            for fold
            in folds
        ),
        "Calibration CV has zero gene overlap",
    )

    raw_metrics = calibration_report[
        "raw_score_metrics"
    ]

    selected_metrics = calibration_report[
        "candidate_metrics_oof"
    ][
        calibration_report[
            "selected_method"
        ]
    ]

    check(
        selected_metrics[
            "brier_score"
        ]
        < raw_metrics[
            "brier_score"
        ],
        "Calibration improves Brier score",
    )

    check(
        selected_metrics[
            "ece"
        ]
        < raw_metrics[
            "ece"
        ],
        "Calibration improves ECE",
    )

    # ========================================================
    # Section 6 — Confidence / uncertainty
    # ========================================================

    print(
        "\n[6] Confidence and uncertainty"
    )

    print(
        "-" * 78
    )

    check(
        calculate_uncertainty(
            0.0
        )
        == 0.0,
        "p=0 has zero entropy uncertainty",
    )

    check(
        calculate_confidence(
            0.0
        )
        == 1.0,
        "p=0 has maximum decision confidence",
    )

    check(
        calculate_uncertainty(
            0.5
        )
        == 1.0,
        "p=0.5 has maximum entropy uncertainty",
    )

    check(
        calculate_confidence(
            0.5
        )
        == 0.0,
        "p=0.5 has zero decision confidence",
    )

    check(
        calculate_uncertainty(
            1.0
        )
        == 0.0,
        "p=1 has zero entropy uncertainty",
    )

    check(
        calculate_confidence(
            1.0
        )
        == 1.0,
        "p=1 has maximum decision confidence",
    )

    confidence_score = float(
        confidence_artifact[
            "confidence_score"
        ]
    )

    uncertainty_score = float(
        confidence_artifact[
            "uncertainty_score"
        ]
    )

    check(
        math.isclose(
            confidence_score
            + uncertainty_score,
            1.0,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ),
        "Confidence and uncertainty sum to 1",
    )

    check(
        confidence_artifact.get(
            "test_set_used"
        )
        is False,
        "Confidence engine did not use the test set",
    )

    # ========================================================
    # Section 7 — Impact mapping
    # ========================================================

    print(
        "\n[7] Impact mapping"
    )

    print(
        "-" * 78
    )

    low_threshold = float(
        impact_mapping[
            "low_threshold"
        ]
    )

    high_threshold = float(
        impact_mapping[
            "high_threshold"
        ]
    )

    check(
        (
            0.0
            <= low_threshold
            < high_threshold
            <= 1.0
        ),
        "Impact thresholds are correctly ordered",
    )

    check(
        impact_mapping[
            "low_region"
        ][
            "fraction"
        ]
        >= 0.05,
        "LOW region satisfies minimum coverage",
    )

    check(
        impact_mapping[
            "high_region"
        ][
            "fraction"
        ]
        >= 0.05,
        "HIGH region satisfies minimum coverage",
    )

    region_rows = (
        int(
            impact_mapping[
                "low_region"
            ][
                "rows"
            ]
        )
        + int(
            impact_mapping[
                "moderate_region"
            ][
                "rows"
            ]
        )
        + int(
            impact_mapping[
                "high_region"
            ][
                "rows"
            ]
        )
    )

    check(
        region_rows
        == int(
            impact_mapping[
                "validation_rows"
            ]
        ),
        "LOW + MODERATE + HIGH rows equal validation rows",
    )

    check(
        map_probability_to_impact(
            0.0,
            impact_mapping,
        )
        == "LOW",
        "Probability 0 maps to LOW",
    )

    midpoint = (
        low_threshold
        + high_threshold
    ) / 2.0

    check(
        map_probability_to_impact(
            midpoint,
            impact_mapping,
        )
        == "MODERATE",
        "Intermediate probability maps to MODERATE",
    )

    check(
        map_probability_to_impact(
            1.0,
            impact_mapping,
        )
        == "HIGH",
        "Probability 1 maps to HIGH",
    )

    check(
        map_probability_to_impact(
            low_threshold,
            impact_mapping,
        )
        == "LOW",
        "LOW threshold boundary maps to LOW",
    )

    check(
        map_probability_to_impact(
            high_threshold,
            impact_mapping,
        )
        == "HIGH",
        "HIGH threshold boundary maps to HIGH",
    )

    check(
        impact_mapping.get(
            "test_set_used"
        )
        is False,
        "Impact mapping did not use the test set",
    )

    # ========================================================
    # Section 8 — Full prediction chain
    # ========================================================

    print(
        "\n[8] End-to-end Sprint 5 chain"
    )

    print(
        "-" * 78
    )

    variant = {
        "reference_allele": "G",
        "alternate_allele": "A",
        "reference_aa": "R",
        "alternate_aa": "H",
        "protein_position": 248,
    }

    prediction = predict_variant(
        variant
    )

    raw_score = float(
        prediction[
            "model_score"
        ]
    )

    calibrated_probability = (
        calibrate_probability(
            raw_score
        )
    )

    confidence_result = (
        evaluate_variant_confidence(
            variant
        )
    )

    impact_result = (
        evaluate_variant_impact(
            variant
        )
    )

    check(
        0.0
        <= raw_score
        <= 1.0,
        "Raw model score lies within [0, 1]",
    )

    check(
        0.0
        <= calibrated_probability
        <= 1.0,
        "Calibrated probability lies within [0, 1]",
    )

    check(
        math.isclose(
            calibrated_probability,
            confidence_result[
                "calibrated_probability"
            ],
            rel_tol=1e-12,
            abs_tol=1e-12,
        ),
        "Calibration and confidence engine use identical probability",
    )

    check(
        math.isclose(
            confidence_result[
                "calibrated_probability"
            ],
            impact_result[
                "calibrated_probability"
            ],
            rel_tol=1e-12,
            abs_tol=1e-12,
        ),
        "Confidence and impact engine use identical probability",
    )

    expected_impact = (
        map_probability_to_impact(
            calibrated_probability,
            impact_mapping,
        )
    )

    check(
        impact_result[
            "impact_class"
        ]
        == expected_impact,
        "Impact result matches frozen probability thresholds",
    )

    check(
        impact_result[
            "impact_class"
        ]
        == "MODERATE",
        "Frozen smoke-test variant maps to MODERATE",
    )

    check(
        impact_result[
            "confidence_band"
        ]
        == "LOW",
        "Frozen smoke-test confidence band is LOW",
    )

    check(
        impact_result.get(
            "research_only"
        )
        is True,
        "End-to-end result remains research-only",
    )

    check(
        impact_result.get(
            "test_set_used"
        )
        is False,
        "End-to-end result indicates no test-set usage",
    )

    # ========================================================
    # Section 9 — Determinism
    # ========================================================

    print(
        "\n[9] Determinism"
    )

    print(
        "-" * 78
    )

    first = (
        evaluate_variant_impact(
            variant
        )
    )

    second = (
        evaluate_variant_impact(
            variant
        )
    )

    check(
        first[
            "raw_model_score"
        ]
        == second[
            "raw_model_score"
        ],
        "Raw prediction is deterministic",
    )

    check(
        first[
            "calibrated_probability"
        ]
        == second[
            "calibrated_probability"
        ],
        "Calibration is deterministic",
    )

    check(
        first[
            "uncertainty_score"
        ]
        == second[
            "uncertainty_score"
        ],
        "Uncertainty is deterministic",
    )

    check(
        first[
            "confidence_score"
        ]
        == second[
            "confidence_score"
        ],
        "Confidence is deterministic",
    )

    check(
        first[
            "impact_class"
        ]
        == second[
            "impact_class"
        ],
        "Impact mapping is deterministic",
    )

    # ========================================================
    # Section 10 — Invalid input guards
    # ========================================================

    print(
        "\n[10] Safety and validation guards"
    )

    print(
        "-" * 78
    )

    check_raises(
        lambda: calibrate_probability(
            -0.1
        ),
        "Calibration rejects probability below 0",
    )

    check_raises(
        lambda: calibrate_probability(
            1.1
        ),
        "Calibration rejects probability above 1",
    )

    check_raises(
        lambda: map_probability_to_impact(
            -0.1
        ),
        "Impact mapper rejects probability below 0",
    )

    check_raises(
        lambda: map_probability_to_impact(
            1.1
        ),
        "Impact mapper rejects probability above 1",
    )

    check_raises(
        lambda: predict_variant(
            {
                "reference_allele": "G",
                "alternate_allele": "G",
                "reference_aa": "R",
                "alternate_aa": "H",
                "protein_position": 248,
            }
        ),
        "Predictor rejects REF = ALT",
    )

    check_raises(
        lambda: predict_variant(
            {
                "reference_allele": "G",
                "alternate_allele": "A",
                "reference_aa": "R",
                "alternate_aa": "R",
                "protein_position": 248,
            }
        ),
        "Predictor rejects unchanged amino acid",
    )

    # ========================================================
    # Section 11 — Semantic separation
    # ========================================================

    print(
        "\n[11] Semantic separation"
    )

    print(
        "-" * 78
    )

    check(
        (
            impact_result[
                "raw_model_score"
            ]
            != impact_result[
                "calibrated_probability"
            ]
        ),
        "Raw model score and calibrated probability remain distinct",
    )

    check(
        (
            impact_result[
                "calibrated_probability"
            ]
            != impact_result[
                "confidence_score"
            ]
        ),
        "Calibrated probability and confidence remain distinct",
    )

    check(
        impact_result[
            "impact_class"
        ]
        in {
            "LOW",
            "MODERATE",
            "HIGH",
        },
        "Impact class uses frozen three-class vocabulary",
    )

    check(
        impact_result[
            "confidence_band"
        ]
        in {
            "LOW",
            "MODERATE",
            "HIGH",
        },
        "Confidence band uses valid vocabulary",
    )

    # ========================================================
    # Final summary
    # ========================================================

    final_summary()


# ============================================================
# Final summary
# ============================================================

def final_summary():

    print(
        "\n"
        + "=" * 78
    )

    print(
        "SPRINT 5 FINAL VERIFICATION SUMMARY"
    )

    print(
        "=" * 78
    )

    print(
        f"Passed checks: {PASSED}"
    )

    print(
        f"Failed checks: {FAILED}"
    )

    if FAILED == 0:

        print(
            "\n✅ SPRINT 5 FINAL VERIFICATION PASSED"
        )

        print(
            "\nSprint 5 can be frozen after "
            "reviewing this output."
        )

    else:

        print(
            "\n❌ SPRINT 5 FINAL VERIFICATION FAILED"
        )

        print(
            "\nFailed checks:"
        )

        for failure in FAILURES:

            print(
                f" - {failure}"
            )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()