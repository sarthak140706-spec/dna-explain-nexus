import json
import math
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score


# ============================================================
# Make project root importable when run as a script
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
    MODEL_ARTIFACT_PATH,
    MODEL_NAME,
    MODEL_VERSION,
    TARGET_INTERPRETATION,
)

from backend.modeling.config import (
    VALIDATION_DATASET_PATH,
    TARGET_COLUMN,
)

from backend.modeling.predictor import (
    FEATURE_COLUMNS,
)

# ============================================================
# Configuration
# ============================================================

RANDOM_SEED = 42

SAMPLE_SIZE = 15000

N_REPEATS = 5

SCORING = "roc_auc"

GLOBAL_IMPORTANCE_PATH = (
    ARTIFACTS_DIR
    / "global_feature_importance_v1.json"
)


# ============================================================
# Load frozen model
# ============================================================

def load_model():

    if not MODEL_ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"Frozen model artifact not found: "
            f"{MODEL_ARTIFACT_PATH}"
        )

    with open(
        MODEL_ARTIFACT_PATH,
        "rb",
    ) as file:

        model = pickle.load(file)

    return model


# ============================================================
# Validation data
# ============================================================

def load_validation_data():

    if not VALIDATION_DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Validation dataset not found: "
            f"{VALIDATION_DATASET_PATH}"
        )

    dataframe = pd.read_csv(
        VALIDATION_DATASET_PATH,
        low_memory=False,
    )

    missing_features = [
        feature
        for feature in FEATURE_COLUMNS
        if feature not in dataframe.columns
    ]

    if missing_features:
        raise ValueError(
            "Validation dataset is missing predictive "
            f"features: {missing_features}"
        )

    if TARGET_COLUMN not in dataframe.columns:
        raise ValueError(
            f"Target column '{TARGET_COLUMN}' "
            "not found in validation dataset."
        )

    return dataframe


# ============================================================
# Stratified validation sample
# ============================================================

def create_stratified_sample(
    dataframe,
):

    if len(dataframe) <= SAMPLE_SIZE:
        return dataframe.copy()

    sampled_parts = []

    class_counts = (
        dataframe[
            TARGET_COLUMN
        ]
        .value_counts()
        .sort_index()
    )

    allocated = 0

    class_values = list(
        class_counts.index
    )

    for index, target_value in enumerate(
        class_values
    ):

        class_data = dataframe[
            dataframe[
                TARGET_COLUMN
            ]
            == target_value
        ]

        if index == len(
            class_values
        ) - 1:

            class_sample_size = (
                SAMPLE_SIZE
                - allocated
            )

        else:

            fraction = (
                len(class_data)
                / len(dataframe)
            )

            class_sample_size = int(
                round(
                    SAMPLE_SIZE
                    * fraction
                )
            )

        class_sample_size = min(
            class_sample_size,
            len(class_data),
        )

        sampled_class = (
            class_data.sample(
                n=class_sample_size,
                random_state=(
                    RANDOM_SEED
                    + int(target_value)
                ),
            )
        )

        sampled_parts.append(
            sampled_class
        )

        allocated += (
            class_sample_size
        )

    sample = pd.concat(
        sampled_parts,
        axis=0,
    )

    sample = sample.sample(
        frac=1.0,
        random_state=RANDOM_SEED,
    ).reset_index(
        drop=True
    )

    return sample


# ============================================================
# Permutation importance
# ============================================================

def calculate_global_importance(
    model,
    dataframe,
):

    X = dataframe[
        FEATURE_COLUMNS
    ].copy()

    y = dataframe[
        TARGET_COLUMN
    ].astype(int)

    baseline_probabilities = (
        model.predict_proba(X)[:, 1]
    )

    baseline_roc_auc = roc_auc_score(
        y,
        baseline_probabilities,
    )

    print(
        f"Baseline sample ROC-AUC: "
        f"{baseline_roc_auc:.4f}"
    )

    result = permutation_importance(
        estimator=model,
        X=X,
        y=y,
        scoring=SCORING,
        n_repeats=N_REPEATS,
        random_state=RANDOM_SEED,
        n_jobs=1,
    )

    rows = []

    for feature, mean, std in zip(
        FEATURE_COLUMNS,
        result.importances_mean,
        result.importances_std,
    ):

        if not math.isfinite(
            float(mean)
        ):
            raise ValueError(
                f"Non-finite importance for "
                f"feature: {feature}"
            )

        if not math.isfinite(
            float(std)
        ):
            raise ValueError(
                f"Non-finite importance standard "
                f"deviation for feature: {feature}"
            )

        rows.append(
            {
                "feature": feature,
                "importance_mean": float(
                    mean
                ),
                "importance_std": float(
                    std
                ),
            }
        )

    rows.sort(
        key=lambda item: (
            item[
                "importance_mean"
            ]
        ),
        reverse=True,
    )

    return (
        float(baseline_roc_auc),
        rows,
    )


# ============================================================
# Save artifact
# ============================================================

def save_importance_report(
    baseline_roc_auc,
    importance_rows,
    full_validation_rows,
    sample,
):

    target_distribution = (
        sample[
            TARGET_COLUMN
        ]
        .value_counts()
        .sort_index()
        .to_dict()
    )

    payload = {
        "artifact_type": (
            "global_permutation_feature_importance"
        ),
        "explanation_version": (
            EXPLANATION_VERSION
        ),
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "target_interpretation": (
            TARGET_INTERPRETATION
        ),
        "evaluation_dataset": (
            "gene-held-out validation split"
        ),
        "test_set_used": False,
        "scoring": SCORING,
        "random_seed": RANDOM_SEED,
        "n_repeats": N_REPEATS,
        "full_validation_rows": int(
            full_validation_rows
        ),
        "sample_rows": int(
            len(sample)
        ),
        "sample_target_distribution": {
            str(key): int(value)
            for key, value
            in target_distribution.items()
        },
        "baseline_sample_roc_auc": (
            baseline_roc_auc
        ),
        "feature_count": len(
            FEATURE_COLUMNS
        ),
        "feature_importance": (
            importance_rows
        ),
        "interpretation": (
            "Permutation importance measures the "
            "change in validation ROC-AUC after "
            "randomly shuffling an input feature. "
            "Larger positive values indicate greater "
            "model reliance. Values near zero suggest "
            "little measurable contribution on this "
            "sample. Negative values can occur when "
            "permuting a feature slightly improves "
            "the evaluation score."
        ),
        "generated_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "research_only": True,
    }

    with open(
        GLOBAL_IMPORTANCE_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )

    return payload


# ============================================================
# Verification
# ============================================================

def verify_report(
    payload,
):

    importances = payload[
        "feature_importance"
    ]

    if payload[
        "feature_count"
    ] != len(FEATURE_COLUMNS):

        raise ValueError(
            "Incorrect feature count."
        )

    if len(importances) != len(
        FEATURE_COLUMNS
    ):

        raise ValueError(
            "Importance report does not contain "
            "all predictive features."
        )

    reported_features = {
        item[
            "feature"
        ]
        for item in importances
    }

    if reported_features != set(
        FEATURE_COLUMNS
    ):

        raise ValueError(
            "Global importance feature schema "
            "does not match the frozen model."
        )

    if payload[
        "test_set_used"
    ] is not False:

        raise ValueError(
            "Test set must not be used for "
            "Sprint 5 XAI development."
        )

    baseline = payload[
        "baseline_sample_roc_auc"
    ]

    if not (
        0.0
        <= baseline
        <= 1.0
    ):

        raise ValueError(
            "Invalid baseline ROC-AUC."
        )


# ============================================================
# Main
# ============================================================

def main():

    print(
        "GeneMirror Sprint 5 "
        "Global Model Explainability"
    )

    print(
        "=" * 65
    )

    print(
        "\nLoading frozen Sprint 4 model..."
    )

    model = load_model()

    print(
        "Model loaded successfully."
    )

    print(
        "\nLoading validation dataset..."
    )

    validation = (
        load_validation_data()
    )

    print(
        f"Validation rows: "
        f"{len(validation):,}"
    )

    print(
        f"Predictive features: "
        f"{len(FEATURE_COLUMNS)}"
    )

    print(
        "\nCreating stratified "
        "explanation sample..."
    )

    sample = (
        create_stratified_sample(
            validation
        )
    )

    print(
        f"Sample rows: "
        f"{len(sample):,}"
    )

    print(
        "\nSample target distribution:"
    )

    distribution = (
        sample[
            TARGET_COLUMN
        ]
        .value_counts()
        .sort_index()
    )

    for target, count in (
        distribution.items()
    ):

        percentage = (
            count
            / len(sample)
            * 100
        )

        print(
            f"Class {target}: "
            f"{count:,} "
            f"({percentage:.2f}%)"
        )

    print(
        "\nCalculating permutation "
        "feature importance..."
    )

    baseline_roc_auc, importance_rows = (
        calculate_global_importance(
            model,
            sample,
        )
    )

    payload = save_importance_report(
        baseline_roc_auc=(
            baseline_roc_auc
        ),
        importance_rows=(
            importance_rows
        ),
        full_validation_rows=(
            len(validation)
        ),
        sample=sample,
    )

    verify_report(
        payload
    )

    print(
        "\nTop 15 global features"
    )

    print(
        "-" * 65
    )

    print(
        f"{'Rank':<6}"
        f"{'Feature':<32}"
        f"{'Importance':>12}"
        f"{'Std':>12}"
    )

    print(
        "-" * 65
    )

    for rank, item in enumerate(
        importance_rows[:15],
        start=1,
    ):

        print(
            f"{rank:<6}"
            f"{item['feature']:<32}"
            f"{item['importance_mean']:>12.6f}"
            f"{item['importance_std']:>12.6f}"
        )

    print(
        "\nOutput:"
    )

    print(
        GLOBAL_IMPORTANCE_PATH
    )

    print(
        "\nTest set used: False"
    )

    print(
        "\n✅ Sprint 5 global model "
        "explainability completed."
    )


if __name__ == "__main__":
    main()