import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd


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
    calculate_raw_scores,
    load_frozen_model,
    load_validation_dataset,
    run_grouped_oof_calibration,
)

from backend.explainability.config import (
    ARTIFACTS_DIR,
    CALIBRATION_VERSION,
    MODEL_NAME,
    MODEL_VERSION,
    TARGET_INTERPRETATION,
)

from backend.explainability.confidence import (
    evaluate_variant_confidence,
)

from backend.modeling.config import (
    TARGET_COLUMN,
)


# ============================================================
# Configuration
# ============================================================

IMPACT_MAPPING_VERSION = (
    "GeneMirror-Impact-Mapping-v1"
)

IMPACT_MAPPING_PATH = (
    ARTIFACTS_DIR
    / "impact_mapping_v1.json"
)

# Each extreme region must represent at least 5%
# of the validation dataset.
MIN_REGION_FRACTION = 0.05

IMPACT_CLASSES = {
    "LOW",
    "MODERATE",
    "HIGH",
}


# ============================================================
# Load selected calibration method
# ============================================================

def load_selected_calibration_method():

    if not CALIBRATION_REPORT_PATH.exists():

        raise FileNotFoundError(
            "Probability calibration report "
            f"not found: {CALIBRATION_REPORT_PATH}"
        )

    with open(
        CALIBRATION_REPORT_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        report = json.load(
            file
        )

    selected_method = report.get(
        "selected_method"
    )

    if selected_method not in {
        "sigmoid",
        "isotonic",
    }:

        raise ValueError(
            "Calibration report contains "
            "an unsupported selected method."
        )

    if report.get(
        "test_set_used"
    ) is not False:

        raise ValueError(
            "Calibration report indicates "
            "test-set usage."
        )

    return selected_method


# ============================================================
# Generate OOF calibrated probabilities
# ============================================================

def generate_oof_probabilities():

    model = load_frozen_model()

    validation = (
        load_validation_dataset()
    )

    targets = (
        validation[
            TARGET_COLUMN
        ]
        .astype(int)
        .to_numpy()
    )

    groups = (
        validation[
            "gene_symbol"
        ]
        .astype(str)
        .to_numpy()
    )

    raw_scores = (
        calculate_raw_scores(
            model,
            validation,
        )
    )

    (
        oof_predictions,
        fold_summaries,
    ) = run_grouped_oof_calibration(
        raw_scores=raw_scores,
        targets=targets,
        groups=groups,
    )

    selected_method = (
        load_selected_calibration_method()
    )

    probabilities = np.asarray(
        oof_predictions[
            selected_method
        ],
        dtype=float,
    )

    if np.isnan(
        probabilities
    ).any():

        raise ValueError(
            "OOF calibrated probabilities "
            "contain missing values."
        )

    if np.any(
        probabilities < 0.0
    ) or np.any(
        probabilities > 1.0
    ):

        raise ValueError(
            "OOF probabilities outside [0, 1]."
        )

    return (
        validation,
        targets,
        probabilities,
        selected_method,
        fold_summaries,
    )


# ============================================================
# Build probability groups
# ============================================================

def build_probability_groups(
    targets,
    probabilities,
):

    dataframe = pd.DataFrame(
        {
            "probability": probabilities,
            "target": targets,
        }
    )

    grouped = (
        dataframe
        .groupby(
            "probability",
            as_index=False,
        )
        .agg(
            rows=(
                "target",
                "size",
            ),
            positives=(
                "target",
                "sum",
            ),
        )
        .sort_values(
            "probability"
        )
        .reset_index(
            drop=True
        )
    )

    grouped[
        "negatives"
    ] = (
        grouped[
            "rows"
        ]
        - grouped[
            "positives"
        ]
    )

    return grouped


# ============================================================
# Derive LOW threshold
# ============================================================

def derive_low_threshold(
    targets,
    probabilities,
):

    grouped = (
        build_probability_groups(
            targets,
            probabilities,
        )
    )

    total_rows = len(
        targets
    )

    grouped[
        "cumulative_rows"
    ] = (
        grouped[
            "rows"
        ].cumsum()
    )

    grouped[
        "cumulative_negatives"
    ] = (
        grouped[
            "negatives"
        ].cumsum()
    )

    grouped[
        "coverage"
    ] = (
        grouped[
            "cumulative_rows"
        ]
        / total_rows
    )

    grouped[
        "benign_like_purity"
    ] = (
        grouped[
            "cumulative_negatives"
        ]
        / grouped[
            "cumulative_rows"
        ]
    )

    candidates = grouped[
        grouped[
            "coverage"
        ]
        >= MIN_REGION_FRACTION
    ].copy()

    if candidates.empty:

        raise ValueError(
            "Unable to derive LOW region "
            "with minimum required coverage."
        )

    # Select the region with the highest
    # benign-like purity while satisfying
    # minimum validation coverage.
    #
    # If several candidates have identical
    # purity, prefer the wider region.
    candidates = candidates.sort_values(
        by=[
            "benign_like_purity",
            "coverage",
        ],
        ascending=[
            False,
            False,
        ],
    )

    selected = (
        candidates.iloc[
            0
        ]
    )

    return {
        "threshold": float(
            selected[
                "probability"
            ]
        ),

        "rows": int(
            selected[
                "cumulative_rows"
            ]
        ),

        "fraction": float(
            selected[
                "coverage"
            ]
        ),

        "benign_like_purity": float(
            selected[
                "benign_like_purity"
            ]
        ),

        "pathogenic_like_rate": float(
            1.0
            - selected[
                "benign_like_purity"
            ]
        ),
    }


# ============================================================
# Derive HIGH threshold
# ============================================================

def derive_high_threshold(
    targets,
    probabilities,
):

    grouped = (
        build_probability_groups(
            targets,
            probabilities,
        )
    )

    total_rows = len(
        targets
    )

    grouped = (
        grouped
        .sort_values(
            "probability",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    grouped[
        "cumulative_rows"
    ] = (
        grouped[
            "rows"
        ].cumsum()
    )

    grouped[
        "cumulative_positives"
    ] = (
        grouped[
            "positives"
        ].cumsum()
    )

    grouped[
        "coverage"
    ] = (
        grouped[
            "cumulative_rows"
        ]
        / total_rows
    )

    grouped[
        "pathogenic_like_purity"
    ] = (
        grouped[
            "cumulative_positives"
        ]
        / grouped[
            "cumulative_rows"
        ]
    )

    candidates = grouped[
        grouped[
            "coverage"
        ]
        >= MIN_REGION_FRACTION
    ].copy()

    if candidates.empty:

        raise ValueError(
            "Unable to derive HIGH region "
            "with minimum required coverage."
        )

    # Select the region with the highest
    # pathogenic-like purity while satisfying
    # minimum validation coverage.
    #
    # If several candidates have identical
    # purity, prefer the wider region.
    candidates = candidates.sort_values(
        by=[
            "pathogenic_like_purity",
            "coverage",
        ],
        ascending=[
            False,
            False,
        ],
    )

    selected = (
        candidates.iloc[
            0
        ]
    )

    return {
        "threshold": float(
            selected[
                "probability"
            ]
        ),

        "rows": int(
            selected[
                "cumulative_rows"
            ]
        ),

        "fraction": float(
            selected[
                "coverage"
            ]
        ),

        "pathogenic_like_purity": float(
            selected[
                "pathogenic_like_purity"
            ]
        ),

        "benign_like_rate": float(
            1.0
            - selected[
                "pathogenic_like_purity"
            ]
        ),
    }


# ============================================================
# Build impact mapping
# ============================================================

def build_impact_mapping():

    (
        validation,
        targets,
        probabilities,
        selected_method,
        fold_summaries,
    ) = generate_oof_probabilities()

    low_metrics = (
        derive_low_threshold(
            targets,
            probabilities,
        )
    )

    high_metrics = (
        derive_high_threshold(
            targets,
            probabilities,
        )
    )

    low_threshold = float(
        low_metrics[
            "threshold"
        ]
    )

    high_threshold = float(
        high_metrics[
            "threshold"
        ]
    )

    if not (
        0.0
        <= low_threshold
        < high_threshold
        <= 1.0
    ):

        raise ValueError(
            "Derived impact thresholds "
            "are not properly ordered."
        )

    low_mask = (
        probabilities
        <= low_threshold
    )

    high_mask = (
        probabilities
        >= high_threshold
    )

    moderate_mask = ~(
        low_mask
        | high_mask
    )

    if (
        low_mask
        & high_mask
    ).any():

        raise ValueError(
            "LOW and HIGH impact regions overlap."
        )

    moderate_rows = int(
        moderate_mask.sum()
    )

    moderate_fraction = float(
        moderate_mask.mean()
    )

    if moderate_rows > 0:

        moderate_positive_rate = float(
            targets[
                moderate_mask
            ].mean()
        )

    else:

        moderate_positive_rate = None

    mapping = {
        "artifact_type": (
            "impact_mapping"
        ),

        "impact_mapping_version": (
            IMPACT_MAPPING_VERSION
        ),

        "calibration_version": (
            CALIBRATION_VERSION
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

        "calibration_method": (
            selected_method
        ),

        "threshold_strategy": (
            "For each extreme region, require "
            "at least 5% OOF validation coverage "
            "and then maximize class-specific "
            "purity. LOW maximizes benign-like "
            "purity; HIGH maximizes pathogenic-like "
            "purity. MODERATE contains the "
            "intermediate region."
        ),

        "minimum_extreme_region_fraction": (
            MIN_REGION_FRACTION
        ),

        "low_threshold": (
            low_threshold
        ),

        "high_threshold": (
            high_threshold
        ),

        "low_region": (
            low_metrics
        ),

        "moderate_region": {
            "rows": (
                moderate_rows
            ),

            "fraction": (
                moderate_fraction
            ),

            "pathogenic_like_rate": (
                moderate_positive_rate
            ),

            "benign_like_rate": (
                (
                    1.0
                    - moderate_positive_rate
                )
                if moderate_positive_rate
                is not None
                else None
            ),
        },

        "high_region": (
            high_metrics
        ),

        "validation_rows": int(
            len(
                validation
            )
        ),

        "validation_genes": int(
            validation[
                "gene_symbol"
            ].nunique()
        ),

        "cv_strategy": (
            "5-fold StratifiedGroupKFold "
            "using gene_symbol"
        ),

        "cv_fold_count": int(
            len(
                fold_summaries
            )
        ),

        "impact_interpretation": (
            "LOW, MODERATE, and HIGH are "
            "computational impact categories "
            "derived from out-of-fold calibrated "
            "ClinVar-proxy probabilities on the "
            "validation dataset. They are not "
            "ClinVar classifications, clinical "
            "diagnoses, probabilities of disease, "
            "or direct measurements of biological "
            "pathogenicity."
        ),

        "threshold_limitation": (
            "The HIGH region has lower proxy-class "
            "purity than the LOW region because the "
            "frozen V1 model provides weaker "
            "separation for pathogenic-like variants. "
            "The thresholds intentionally reflect "
            "observed validation performance rather "
            "than imposing arbitrary symmetric "
            "cutoffs."
        ),

        "test_set_used": False,

        "research_only": True,

        "created_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }

    return mapping


# ============================================================
# Save / load mapping
# ============================================================

def save_impact_mapping(
    mapping,
):

    with open(
        IMPACT_MAPPING_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            mapping,
            file,
            indent=2,
        )


def load_impact_mapping():

    if not IMPACT_MAPPING_PATH.exists():

        raise FileNotFoundError(
            f"Impact mapping not found: "
            f"{IMPACT_MAPPING_PATH}"
        )

    with open(
        IMPACT_MAPPING_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        mapping = json.load(
            file
        )

    return mapping


# ============================================================
# Probability -> impact class
# ============================================================

def map_probability_to_impact(
    calibrated_probability,
    mapping=None,
):

    try:

        calibrated_probability = float(
            calibrated_probability
        )

    except (
        TypeError,
        ValueError,
    ) as error:

        raise ValueError(
            "Calibrated probability "
            "must be numeric."
        ) from error

    if not math.isfinite(
        calibrated_probability
    ):

        raise ValueError(
            "Calibrated probability "
            "must be finite."
        )

    if not (
        0.0
        <= calibrated_probability
        <= 1.0
    ):

        raise ValueError(
            "Calibrated probability "
            "must lie within [0, 1]."
        )

    if mapping is None:

        mapping = (
            load_impact_mapping()
        )

    low_threshold = float(
        mapping[
            "low_threshold"
        ]
    )

    high_threshold = float(
        mapping[
            "high_threshold"
        ]
    )

    if not (
        0.0
        <= low_threshold
        < high_threshold
        <= 1.0
    ):

        raise ValueError(
            "Stored impact thresholds "
            "are invalid."
        )

    if (
        calibrated_probability
        <= low_threshold
    ):

        return "LOW"

    if (
        calibrated_probability
        >= high_threshold
    ):

        return "HIGH"

    return "MODERATE"


# ============================================================
# Variant-level helper
# ============================================================

def evaluate_variant_impact(
    variant: Dict[str, Any],
):

    confidence_result = (
        evaluate_variant_confidence(
            variant
        )
    )

    impact_class = (
        map_probability_to_impact(
            confidence_result[
                "calibrated_probability"
            ]
        )
    )

    result = {
        **confidence_result,

        "impact_class": (
            impact_class
        ),

        "impact_mapping_version": (
            IMPACT_MAPPING_VERSION
        ),

        "impact_interpretation": (
            "Computational impact category "
            "derived from the calibrated "
            "ClinVar-proxy probability. "
            "It is not a clinical classification "
            "or diagnostic conclusion."
        ),
    }

    return result


# ============================================================
# Verification
# ============================================================

def verify_impact_mapping(
    mapping,
):

    low_threshold = float(
        mapping[
            "low_threshold"
        ]
    )

    high_threshold = float(
        mapping[
            "high_threshold"
        ]
    )

    if not (
        0.0
        <= low_threshold
        < high_threshold
        <= 1.0
    ):

        raise ValueError(
            "Impact thresholds are invalid."
        )

    if (
        mapping[
            "low_region"
        ][
            "fraction"
        ]
        < MIN_REGION_FRACTION
    ):

        raise ValueError(
            "LOW region coverage is below "
            "the required minimum."
        )

    if (
        mapping[
            "high_region"
        ][
            "fraction"
        ]
        < MIN_REGION_FRACTION
    ):

        raise ValueError(
            "HIGH region coverage is below "
            "the required minimum."
        )

    low_rows = int(
        mapping[
            "low_region"
        ][
            "rows"
        ]
    )

    moderate_rows = int(
        mapping[
            "moderate_region"
        ][
            "rows"
        ]
    )

    high_rows = int(
        mapping[
            "high_region"
        ][
            "rows"
        ]
    )

    validation_rows = int(
        mapping[
            "validation_rows"
        ]
    )

    if (
        low_rows
        + moderate_rows
        + high_rows
        != validation_rows
    ):

        raise ValueError(
            "Impact region row counts "
            "do not sum to validation rows."
        )

    if mapping[
        "test_set_used"
    ] is not False:

        raise ValueError(
            "Test set must remain unused."
        )

    if (
        map_probability_to_impact(
            0.0,
            mapping,
        )
        != "LOW"
    ):

        raise ValueError(
            "Lower probability boundary "
            "must map to LOW."
        )

    if (
        map_probability_to_impact(
            1.0,
            mapping,
        )
        != "HIGH"
    ):

        raise ValueError(
            "Upper probability boundary "
            "must map to HIGH."
        )

    midpoint = (
        low_threshold
        + high_threshold
    ) / 2.0

    if (
        map_probability_to_impact(
            midpoint,
            mapping,
        )
        != "MODERATE"
    ):

        raise ValueError(
            "Intermediate probability "
            "must map to MODERATE."
        )

    if (
        map_probability_to_impact(
            low_threshold,
            mapping,
        )
        != "LOW"
    ):

        raise ValueError(
            "LOW threshold boundary "
            "mapping failed."
        )

    if (
        map_probability_to_impact(
            high_threshold,
            mapping,
        )
        != "HIGH"
    ):

        raise ValueError(
            "HIGH threshold boundary "
            "mapping failed."
        )


# ============================================================
# Main
# ============================================================

def main():

    print(
        "GeneMirror Sprint 5 "
        "LOW / MODERATE / HIGH Impact Mapping"
    )

    print(
        "=" * 82
    )

    print(
        "\nGenerating validation-derived "
        "OOF calibrated probabilities..."
    )

    mapping = (
        build_impact_mapping()
    )

    print(
        "Thresholds derived successfully."
    )

    print(
        "\nVerifying impact mapping..."
    )

    verify_impact_mapping(
        mapping
    )

    print(
        "Impact mapping verified."
    )

    save_impact_mapping(
        mapping
    )

    print(
        "\nDerived thresholds"
    )

    print(
        "-" * 70
    )

    print(
        f"LOW:       p <= "
        f"{mapping['low_threshold']:.6f}"
    )

    print(
        f"MODERATE:  "
        f"{mapping['low_threshold']:.6f} "
        f"< p < "
        f"{mapping['high_threshold']:.6f}"
    )

    print(
        f"HIGH:      p >= "
        f"{mapping['high_threshold']:.6f}"
    )

    print(
        "\nValidation region quality"
    )

    print(
        "-" * 70
    )

    print(
        "LOW rows: "
        f"{mapping['low_region']['rows']:,}"
    )

    print(
        "LOW coverage: "
        f"{mapping['low_region']['fraction']:.2%}"
    )

    print(
        "LOW benign-like purity: "
        f"{mapping['low_region']['benign_like_purity']:.2%}"
    )

    print(
        "\nMODERATE rows: "
        f"{mapping['moderate_region']['rows']:,}"
    )

    print(
        "MODERATE coverage: "
        f"{mapping['moderate_region']['fraction']:.2%}"
    )

    if (
        mapping[
            "moderate_region"
        ][
            "pathogenic_like_rate"
        ]
        is not None
    ):

        print(
            "MODERATE pathogenic-like rate: "
            f"{mapping['moderate_region']['pathogenic_like_rate']:.2%}"
        )

    print(
        "\nHIGH rows: "
        f"{mapping['high_region']['rows']:,}"
    )

    print(
        "HIGH coverage: "
        f"{mapping['high_region']['fraction']:.2%}"
    )

    print(
        "HIGH pathogenic-like purity: "
        f"{mapping['high_region']['pathogenic_like_purity']:.2%}"
    )

    print(
        "\nTesting example variant..."
    )

    variant = {
        "reference_allele": "G",
        "alternate_allele": "A",
        "reference_aa": "R",
        "alternate_aa": "H",
        "protein_position": 248,
    }

    result = (
        evaluate_variant_impact(
            variant
        )
    )

    print(
        f"Calibrated probability: "
        f"{result['calibrated_probability']:.6f}"
    )

    print(
        f"Impact class: "
        f"{result['impact_class']}"
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
        mapping[
            "test_set_used"
        ],
    )

    print(
        "\nOutput:"
    )

    print(
        IMPACT_MAPPING_PATH
    )

    print(
        "\nImportant:"
    )

    print(
        "LOW / MODERATE / HIGH are "
        "validation-derived computational "
        "impact categories."
    )

    print(
        "They are NOT clinical "
        "pathogenicity classifications."
    )

    print(
        "\n✅ Sprint 5 impact mapping "
        "completed."
    )


if __name__ == "__main__":
    main()