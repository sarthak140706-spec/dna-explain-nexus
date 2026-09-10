import json
import math
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import (
    StratifiedGroupKFold,
)


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
    CALIBRATION_VERSION,
    MODEL_ARTIFACT_PATH,
    MODEL_NAME,
    MODEL_VERSION,
    TARGET_INTERPRETATION,
)

from backend.modeling.config import (
    TARGET_COLUMN,
    VALIDATION_DATASET_PATH,
)

from backend.modeling.predictor import (
    FEATURE_COLUMNS,
)


# ============================================================
# Configuration
# ============================================================

GROUP_COLUMN = "gene_symbol"

RANDOM_SEED = 42

N_SPLITS = 5

ECE_BINS = 10

CALIBRATOR_PATH = (
    ARTIFACTS_DIR
    / "probability_calibrator_v1.pkl"
)

CALIBRATION_REPORT_PATH = (
    ARTIFACTS_DIR
    / "probability_calibration_report_v1.json"
)

SUPPORTED_METHODS = {
    "sigmoid",
    "isotonic",
}


# ============================================================
# Frozen Sprint 4 model
# ============================================================

def load_frozen_model():

    if not MODEL_ARTIFACT_PATH.exists():

        raise FileNotFoundError(
            f"Frozen Sprint 4 model not found: "
            f"{MODEL_ARTIFACT_PATH}"
        )

    with open(
        MODEL_ARTIFACT_PATH,
        "rb",
    ) as file:

        model = pickle.load(
            file
        )

    return model


# ============================================================
# Validation dataset
# ============================================================

def load_validation_dataset():

    if not VALIDATION_DATASET_PATH.exists():

        raise FileNotFoundError(
            f"Validation dataset not found: "
            f"{VALIDATION_DATASET_PATH}"
        )

    validation = pd.read_csv(
        VALIDATION_DATASET_PATH,
        low_memory=False,
    )

    required_columns = (
        list(FEATURE_COLUMNS)
        + [
            TARGET_COLUMN,
            GROUP_COLUMN,
        ]
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in validation.columns
    ]

    if missing_columns:

        raise ValueError(
            "Validation dataset missing "
            f"required columns: "
            f"{missing_columns}"
        )

    if validation[
        TARGET_COLUMN
    ].isna().any():

        raise ValueError(
            "Validation target contains "
            "missing values."
        )

    if validation[
        GROUP_COLUMN
    ].isna().any():

        raise ValueError(
            "Validation gene groups "
            "contain missing values."
        )

    target_values = set(
        validation[
            TARGET_COLUMN
        ]
        .astype(int)
        .unique()
        .tolist()
    )

    if target_values != {
        0,
        1,
    }:

        raise ValueError(
            "Calibration requires exactly "
            "target classes 0 and 1."
        )

    return validation


# ============================================================
# Raw model scores
# ============================================================

def calculate_raw_scores(
    model,
    dataframe,
):

    X = dataframe[
        FEATURE_COLUMNS
    ]

    probabilities = (
        model.predict_proba(
            X
        )
    )

    raw_scores = np.asarray(
        probabilities[:, 1],
        dtype=float,
    )

    if not np.all(
        np.isfinite(
            raw_scores
        )
    ):

        raise ValueError(
            "Raw model scores contain "
            "non-finite values."
        )

    if np.any(
        raw_scores < 0.0
    ) or np.any(
        raw_scores > 1.0
    ):

        raise ValueError(
            "Raw model scores outside "
            "[0, 1]."
        )

    return raw_scores


# ============================================================
# Expected Calibration Error
# ============================================================

def expected_calibration_error(
    y_true,
    probabilities,
    n_bins=ECE_BINS,
):

    y_true = np.asarray(
        y_true,
        dtype=int,
    )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    if len(
        y_true
    ) != len(
        probabilities
    ):

        raise ValueError(
            "Target and probability "
            "lengths do not match."
        )

    bin_edges = np.linspace(
        0.0,
        1.0,
        n_bins + 1,
    )

    total_count = len(
        probabilities
    )

    ece = 0.0

    for index in range(
        n_bins
    ):

        lower = (
            bin_edges[
                index
            ]
        )

        upper = (
            bin_edges[
                index + 1
            ]
        )

        if index == (
            n_bins - 1
        ):

            mask = (
                (probabilities >= lower)
                & (probabilities <= upper)
            )

        else:

            mask = (
                (probabilities >= lower)
                & (probabilities < upper)
            )

        count = int(
            mask.sum()
        )

        if count == 0:

            continue

        mean_probability = float(
            probabilities[
                mask
            ].mean()
        )

        observed_rate = float(
            y_true[
                mask
            ].mean()
        )

        bin_error = abs(
            mean_probability
            - observed_rate
        )

        weight = (
            count
            / total_count
        )

        ece += (
            weight
            * bin_error
        )

    return float(
        ece
    )


# ============================================================
# Calibration metrics
# ============================================================

def calculate_metrics(
    y_true,
    probabilities,
):

    y_true = np.asarray(
        y_true,
        dtype=int,
    )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    return {
        "brier_score": float(
            brier_score_loss(
                y_true,
                probabilities,
            )
        ),

        "log_loss": float(
            log_loss(
                y_true,
                probabilities,
                labels=[
                    0,
                    1,
                ],
            )
        ),

        "roc_auc": float(
            roc_auc_score(
                y_true,
                probabilities,
            )
        ),

        "ece": float(
            expected_calibration_error(
                y_true,
                probabilities,
            )
        ),

        "mean_probability": float(
            probabilities.mean()
        ),

        "observed_positive_rate": float(
            y_true.mean()
        ),
    }


# ============================================================
# Calibrator creation
# ============================================================

def create_calibrator(
    method,
):

    if method == "sigmoid":

        return LogisticRegression(
            solver="lbfgs",
            max_iter=1000,
            random_state=RANDOM_SEED,
        )

    if method == "isotonic":

        return IsotonicRegression(
            out_of_bounds="clip",
        )

    raise ValueError(
        f"Unsupported calibration "
        f"method: {method}"
    )


# ============================================================
# Fit calibrator
# ============================================================

def fit_calibrator(
    method,
    raw_scores,
    targets,
):

    calibrator = create_calibrator(
        method
    )

    raw_scores = np.asarray(
        raw_scores,
        dtype=float,
    )

    targets = np.asarray(
        targets,
        dtype=int,
    )

    if method == "sigmoid":

        calibrator.fit(
            raw_scores.reshape(
                -1,
                1,
            ),
            targets,
        )

    elif method == "isotonic":

        calibrator.fit(
            raw_scores,
            targets,
        )

    else:

        raise ValueError(
            f"Unsupported calibration "
            f"method: {method}"
        )

    return calibrator


# ============================================================
# Apply calibrator
# ============================================================

def apply_calibrator(
    calibrator,
    method,
    raw_scores,
):

    raw_scores = np.asarray(
        raw_scores,
        dtype=float,
    )

    if method == "sigmoid":

        calibrated = (
            calibrator.predict_proba(
                raw_scores.reshape(
                    -1,
                    1,
                )
            )[:, 1]
        )

    elif method == "isotonic":

        calibrated = (
            calibrator.predict(
                raw_scores
            )
        )

    else:

        raise ValueError(
            f"Unsupported calibration "
            f"method: {method}"
        )

    calibrated = np.asarray(
        calibrated,
        dtype=float,
    )

    calibrated = np.clip(
        calibrated,
        0.0,
        1.0,
    )

    return calibrated


# ============================================================
# Gene-grouped OOF calibration
# ============================================================

def run_grouped_oof_calibration(
    raw_scores,
    targets,
    groups,
):

    raw_scores = np.asarray(
        raw_scores,
        dtype=float,
    )

    targets = np.asarray(
        targets,
        dtype=int,
    )

    groups = np.asarray(
        groups,
    )

    splitter = (
        StratifiedGroupKFold(
            n_splits=N_SPLITS,
            shuffle=True,
            random_state=RANDOM_SEED,
        )
    )

    oof_predictions = {
        method: np.full(
            len(targets),
            np.nan,
            dtype=float,
        )
        for method
        in SUPPORTED_METHODS
    }

    fold_summaries = []

    dummy_X = (
        raw_scores.reshape(
            -1,
            1,
        )
    )

    for fold_number, (
        fit_indices,
        eval_indices,
    ) in enumerate(
        splitter.split(
            dummy_X,
            targets,
            groups,
        ),
        start=1,
    ):

        fit_targets = (
            targets[
                fit_indices
            ]
        )

        eval_targets = (
            targets[
                eval_indices
            ]
        )

        if len(
            np.unique(
                fit_targets
            )
        ) != 2:

            raise ValueError(
                f"Calibration fold "
                f"{fold_number} fit partition "
                "does not contain both classes."
            )

        if len(
            np.unique(
                eval_targets
            )
        ) != 2:

            raise ValueError(
                f"Calibration fold "
                f"{fold_number} evaluation "
                "partition does not contain "
                "both classes."
            )

        fit_groups = set(
            groups[
                fit_indices
            ]
        )

        eval_groups = set(
            groups[
                eval_indices
            ]
        )

        group_overlap = (
            fit_groups
            & eval_groups
        )

        if group_overlap:

            raise ValueError(
                f"Gene leakage detected "
                f"in calibration fold "
                f"{fold_number}."
            )

        for method in sorted(
            SUPPORTED_METHODS
        ):

            calibrator = (
                fit_calibrator(
                    method=method,
                    raw_scores=(
                        raw_scores[
                            fit_indices
                        ]
                    ),
                    targets=(
                        fit_targets
                    ),
                )
            )

            fold_probabilities = (
                apply_calibrator(
                    calibrator=calibrator,
                    method=method,
                    raw_scores=(
                        raw_scores[
                            eval_indices
                        ]
                    ),
                )
            )

            oof_predictions[
                method
            ][
                eval_indices
            ] = (
                fold_probabilities
            )

        fold_summaries.append(
            {
                "fold": (
                    fold_number
                ),

                "fit_rows": int(
                    len(
                        fit_indices
                    )
                ),

                "evaluation_rows": int(
                    len(
                        eval_indices
                    )
                ),

                "fit_genes": int(
                    len(
                        fit_groups
                    )
                ),

                "evaluation_genes": int(
                    len(
                        eval_groups
                    )
                ),

                "gene_overlap": int(
                    len(
                        group_overlap
                    )
                ),

                "evaluation_positive_rate": float(
                    eval_targets.mean()
                ),
            }
        )

    for method, values in (
        oof_predictions.items()
    ):

        if np.isnan(
            values
        ).any():

            raise ValueError(
                f"OOF calibration predictions "
                f"incomplete for method: "
                f"{method}"
            )

    return (
        oof_predictions,
        fold_summaries,
    )


# ============================================================
# Method selection
# ============================================================

def select_best_method(
    candidate_metrics:
    Dict[str, Dict[str, float]],
):

    if not candidate_metrics:

        raise ValueError(
            "No calibration methods "
            "were evaluated."
        )

    selected_method = min(
        candidate_metrics,
        key=lambda method: (
            candidate_metrics[
                method
            ][
                "brier_score"
            ],
            candidate_metrics[
                method
            ][
                "log_loss"
            ],
            candidate_metrics[
                method
            ][
                "ece"
            ],
        ),
    )

    return selected_method


# ============================================================
# Build final calibration
# ============================================================

def build_probability_calibrator():

    print(
        "Loading frozen Sprint 4 model..."
    )

    model = load_frozen_model()

    print(
        "Model loaded successfully."
    )

    print(
        "\nLoading validation dataset..."
    )

    validation = (
        load_validation_dataset()
    )

    print(
        f"Validation rows: "
        f"{len(validation):,}"
    )

    print(
        f"Validation genes: "
        f"{validation[GROUP_COLUMN].nunique():,}"
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
            GROUP_COLUMN
        ]
        .astype(str)
        .to_numpy()
    )

    print(
        "\nGenerating frozen model "
        "raw scores..."
    )

    raw_scores = (
        calculate_raw_scores(
            model,
            validation,
        )
    )

    raw_metrics = (
        calculate_metrics(
            targets,
            raw_scores,
        )
    )

    print(
        f"Raw ROC-AUC: "
        f"{raw_metrics['roc_auc']:.4f}"
    )

    print(
        f"Raw Brier score: "
        f"{raw_metrics['brier_score']:.6f}"
    )

    print(
        f"Raw log loss: "
        f"{raw_metrics['log_loss']:.6f}"
    )

    print(
        f"Raw ECE: "
        f"{raw_metrics['ece']:.6f}"
    )

    print(
        "\nRunning 5-fold "
        "gene-grouped OOF calibration..."
    )

    (
        oof_predictions,
        fold_summaries,
    ) = run_grouped_oof_calibration(
        raw_scores=raw_scores,
        targets=targets,
        groups=groups,
    )

    candidate_metrics = {}

    for method in sorted(
        SUPPORTED_METHODS
    ):

        candidate_metrics[
            method
        ] = (
            calculate_metrics(
                targets,
                oof_predictions[
                    method
                ],
            )
        )

    selected_method = (
        select_best_method(
            candidate_metrics
        )
    )

    print(
        "\nCalibration comparison"
    )

    print(
        "-" * 78
    )

    print(
        f"{'Method':<14}"
        f"{'Brier':>12}"
        f"{'LogLoss':>12}"
        f"{'ECE':>12}"
        f"{'ROC-AUC':>12}"
    )

    print(
        "-" * 78
    )

    print(
        f"{'raw':<14}"
        f"{raw_metrics['brier_score']:>12.6f}"
        f"{raw_metrics['log_loss']:>12.6f}"
        f"{raw_metrics['ece']:>12.6f}"
        f"{raw_metrics['roc_auc']:>12.4f}"
    )

    for method in sorted(
        SUPPORTED_METHODS
    ):

        metrics = (
            candidate_metrics[
                method
            ]
        )

        print(
            f"{method:<14}"
            f"{metrics['brier_score']:>12.6f}"
            f"{metrics['log_loss']:>12.6f}"
            f"{metrics['ece']:>12.6f}"
            f"{metrics['roc_auc']:>12.4f}"
        )

    print(
        f"\nSelected calibration method: "
        f"{selected_method}"
    )

    print(
        "\nRefitting selected calibrator "
        "on full validation split..."
    )

    final_calibrator = (
        fit_calibrator(
            method=selected_method,
            raw_scores=raw_scores,
            targets=targets,
        )
    )

    final_validation_probabilities = (
        apply_calibrator(
            calibrator=final_calibrator,
            method=selected_method,
            raw_scores=raw_scores,
        )
    )

    final_fit_metrics = (
        calculate_metrics(
            targets,
            final_validation_probabilities,
        )
    )

    artifact = {
        "artifact_type": (
            "probability_calibrator"
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

        "selected_method": (
            selected_method
        ),

        "calibrator": (
            final_calibrator
        ),

        "positive_class": 1,

        "positive_class_name": (
            "pathogenic_like"
        ),

        "target_interpretation": (
            TARGET_INTERPRETATION
        ),

        "probability_interpretation": (
            "Calibrated probability of the "
            "ClinVar-derived pathogenic-like "
            "proxy class. This is not a "
            "clinical probability, disease "
            "probability, or confidence score."
        ),

        "fit_dataset": (
            "gene-held-out validation split"
        ),

        "test_set_used": False,

        "research_only": True,
    }

    report = {
        "artifact_type": (
            "probability_calibration_report"
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

        "validation_rows": int(
            len(
                validation
            )
        ),

        "validation_genes": int(
            validation[
                GROUP_COLUMN
            ].nunique()
        ),

        "validation_positive_rate": float(
            targets.mean()
        ),

        "cv_strategy": (
            "5-fold StratifiedGroupKFold "
            "using gene_symbol"
        ),

        "cv_folds": (
            fold_summaries
        ),

        "raw_score_metrics": (
            raw_metrics
        ),

        "candidate_metrics_oof": (
            candidate_metrics
        ),

        "selection_primary_metric": (
            "brier_score"
        ),

        "selection_secondary_metrics": [
            "log_loss",
            "ece",
        ],

        "selected_method": (
            selected_method
        ),

        "final_full_validation_fit_metrics": (
            final_fit_metrics
        ),

        "probability_interpretation": (
            "Calibrated probability of the "
            "ClinVar-derived pathogenic-like "
            "proxy class. It must not be "
            "interpreted as probability of "
            "disease, clinical pathogenicity, "
            "or prediction confidence."
        ),

        "test_set_used": False,

        "research_only": True,

        "created_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }

    return (
        artifact,
        report,
    )


# ============================================================
# Save artifacts
# ============================================================

def save_calibration_artifacts(
    artifact,
    report,
):

    with open(
        CALIBRATOR_PATH,
        "wb",
    ) as file:

        pickle.dump(
            artifact,
            file,
        )

    with open(
        CALIBRATION_REPORT_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )


# ============================================================
# Load saved calibrator
# ============================================================

def load_probability_calibrator():

    if not CALIBRATOR_PATH.exists():

        raise FileNotFoundError(
            f"Calibration artifact not found: "
            f"{CALIBRATOR_PATH}"
        )

    with open(
        CALIBRATOR_PATH,
        "rb",
    ) as file:

        artifact = pickle.load(
            file
        )

    required_keys = {
        "selected_method",
        "calibrator",
        "test_set_used",
    }

    missing = (
        required_keys
        - set(
            artifact.keys()
        )
    )

    if missing:

        raise ValueError(
            "Calibration artifact missing "
            f"required keys: "
            f"{sorted(missing)}"
        )

    if artifact[
        "selected_method"
    ] not in SUPPORTED_METHODS:

        raise ValueError(
            "Saved calibration artifact "
            "contains unsupported method."
        )

    if artifact[
        "test_set_used"
    ] is not False:

        raise ValueError(
            "Calibration artifact indicates "
            "test-set usage."
        )

    return artifact


# ============================================================
# Public probability function
# ============================================================

def calibrate_probability(
    raw_model_score,
):

    try:

        raw_model_score = float(
            raw_model_score
        )

    except (
        TypeError,
        ValueError,
    ) as error:

        raise ValueError(
            "Raw model score must be numeric."
        ) from error

    if not math.isfinite(
        raw_model_score
    ):

        raise ValueError(
            "Raw model score must be finite."
        )

    if not (
        0.0
        <= raw_model_score
        <= 1.0
    ):

        raise ValueError(
            "Raw model score must be "
            "between 0 and 1."
        )

    artifact = (
        load_probability_calibrator()
    )

    calibrated = (
        apply_calibrator(
            calibrator=artifact[
                "calibrator"
            ],
            method=artifact[
                "selected_method"
            ],
            raw_scores=np.array(
                [
                    raw_model_score
                ],
                dtype=float,
            ),
        )
    )

    return float(
        calibrated[
            0
        ]
    )


# ============================================================
# Verification
# ============================================================

def verify_calibration(
    artifact,
    report,
):

    if report[
        "test_set_used"
    ] is not False:

        raise ValueError(
            "Test set was used during "
            "probability calibration."
        )

    if artifact[
        "test_set_used"
    ] is not False:

        raise ValueError(
            "Calibration artifact indicates "
            "test-set usage."
        )

    if report[
        "validation_rows"
    ] <= 0:

        raise ValueError(
            "Invalid validation row count."
        )

    if report[
        "validation_genes"
    ] <= 0:

        raise ValueError(
            "Invalid validation gene count."
        )

    if len(
        report[
            "cv_folds"
        ]
    ) != N_SPLITS:

        raise ValueError(
            "Unexpected number of "
            "calibration folds."
        )

    for fold in report[
        "cv_folds"
    ]:

        if fold[
            "gene_overlap"
        ] != 0:

            raise ValueError(
                "Gene leakage found in "
                "calibration CV."
            )

    selected_method = (
        report[
            "selected_method"
        ]
    )

    if selected_method not in (
        SUPPORTED_METHODS
    ):

        raise ValueError(
            "Invalid selected "
            "calibration method."
        )

    for method, metrics in (
        report[
            "candidate_metrics_oof"
        ].items()
    ):

        for metric_name in [
            "brier_score",
            "log_loss",
            "roc_auc",
            "ece",
            "mean_probability",
            "observed_positive_rate",
        ]:

            value = float(
                metrics[
                    metric_name
                ]
            )

            if not math.isfinite(
                value
            ):

                raise ValueError(
                    f"Non-finite calibration "
                    f"metric: {method} "
                    f"{metric_name}"
                )

    print(
        "\nCalibration verification passed."
    )


# ============================================================
# Main
# ============================================================

def main():

    print(
        "GeneMirror Sprint 5 "
        "Probability Calibration"
    )

    print(
        "=" * 78
    )

    (
        artifact,
        report,
    ) = build_probability_calibrator()

    print(
        "\nVerifying calibration..."
    )

    verify_calibration(
        artifact,
        report,
    )

    print(
        "\nSaving calibration artifacts..."
    )

    save_calibration_artifacts(
        artifact,
        report,
    )

    print(
        "\nCalibration artifact:"
    )

    print(
        CALIBRATOR_PATH
    )

    print(
        "\nCalibration report:"
    )

    print(
        CALIBRATION_REPORT_PATH
    )

    print(
        "\nTest set used:",
        report[
            "test_set_used"
        ],
    )

    print(
        "\nImportant:"
    )

    print(
        "The calibrated value represents "
        "the probability of the "
        "ClinVar-derived pathogenic-like "
        "proxy target."
    )

    print(
        "It is NOT clinical pathogenicity "
        "probability, disease probability, "
        "or model confidence."
    )

    print(
        "\n✅ Sprint 5 probability "
        "calibration completed."
    )


if __name__ == "__main__":
    main()