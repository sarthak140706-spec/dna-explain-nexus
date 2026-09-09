import json
import pickle

import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    matthews_corrcoef,
    confusion_matrix,
    classification_report,
)

from config import (
    PROJECT_ROOT,
    TEST_DATASET_PATH,
)

from features import (
    NUMERIC_FEATURE_COLUMNS,
    CATEGORICAL_FEATURE_COLUMNS,
)


# ============================================================
# Paths
# ============================================================

MODEL_DIR = (
    PROJECT_ROOT
    / "backend"
    / "modeling"
    / "artifacts"
)

MAIN_MODEL_PATH = (
    MODEL_DIR
    / "hist_gradient_boosting_v1.pkl"
)

FINAL_METRICS_PATH = (
    MODEL_DIR
    / "final_test_metrics_v1.json"
)


# ============================================================
# Exact selected model features
# ============================================================

NUMERIC_FEATURES = [
    feature
    for feature in NUMERIC_FEATURE_COLUMNS
    if feature != "protein_position_log"
]

FEATURE_COLUMNS = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURE_COLUMNS
)

TARGET_COLUMN = "target_label"


# ============================================================
# Load selected frozen model
# ============================================================

def load_model():

    if not MAIN_MODEL_PATH.exists():

        raise FileNotFoundError(
            "Selected model artifact not found:\n"
            f"{MAIN_MODEL_PATH}"
        )

    with open(
        MAIN_MODEL_PATH,
        "rb",
    ) as file:

        model = pickle.load(
            file
        )

    return model


# ============================================================
# Load frozen test set
# ============================================================

def load_test_dataset():

    if not TEST_DATASET_PATH.exists():

        raise FileNotFoundError(
            "Test dataset not found:\n"
            f"{TEST_DATASET_PATH}"
        )

    dataframe = pd.read_csv(
        TEST_DATASET_PATH,
        low_memory=False,
    )

    return dataframe


# ============================================================
# Validate test set
# ============================================================

def validate_test_dataset(
    dataframe: pd.DataFrame,
):

    required_columns = (
        FEATURE_COLUMNS
        + [
            TARGET_COLUMN,
            "variant_key",
            "gene_symbol",
        ]
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:

        raise KeyError(
            "Test dataset missing columns:\n"
            + "\n".join(missing_columns)
        )

    missing_features = int(
        dataframe[
            FEATURE_COLUMNS
        ]
        .isna()
        .sum()
        .sum()
    )

    if missing_features != 0:

        raise ValueError(
            f"Test dataset contains "
            f"{missing_features} missing "
            "feature values."
        )

    duplicate_variants = int(
        dataframe[
            "variant_key"
        ]
        .duplicated()
        .sum()
    )

    if duplicate_variants != 0:

        raise ValueError(
            f"Test dataset contains "
            f"{duplicate_variants} duplicate variants."
        )

    targets = set(
        dataframe[
            TARGET_COLUMN
        ]
        .astype(int)
        .unique()
    )

    if targets != {0, 1}:

        raise ValueError(
            f"Unexpected test targets: "
            f"{targets}"
        )


# ============================================================
# Final evaluation
# ============================================================

def evaluate_final_model():

    print(
        "GeneMirror Final Held-Out Test Evaluation"
    )

    print(
        "=" * 65
    )

    print(
        "\nSelected model:"
    )

    print(
        "HistGradientBoostingClassifier"
    )

    print(
        "\nModel artifact:"
    )

    print(
        MAIN_MODEL_PATH
    )

    print(
        "\nFrozen test dataset:"
    )

    print(
        TEST_DATASET_PATH
    )

    model = load_model()

    test = load_test_dataset()

    validate_test_dataset(
        test
    )

    print(
        f"\nTest rows: "
        f"{len(test):,}"
    )

    print(
        f"Held-out genes: "
        f"{test['gene_symbol'].nunique():,}"
    )

    benign_count = int(
        (
            test[
                TARGET_COLUMN
            ]
            == 0
        ).sum()
    )

    pathogenic_count = int(
        (
            test[
                TARGET_COLUMN
            ]
            == 1
        ).sum()
    )

    print(
        f"Benign-like: "
        f"{benign_count:,}"
    )

    print(
        f"Pathogenic-like: "
        f"{pathogenic_count:,}"
    )

    # --------------------------------------------------------
    # Predict
    # --------------------------------------------------------

    X_test = test[
        FEATURE_COLUMNS
    ]

    y_true = test[
        TARGET_COLUMN
    ].astype(int)

    print(
        "\nRunning final predictions..."
    )

    y_pred = model.predict(
        X_test
    )

    y_probability = (
        model.predict_proba(
            X_test
        )[:, 1]
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    balanced_accuracy = (
        balanced_accuracy_score(
            y_true,
            y_pred,
        )
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_true,
        y_probability,
    )

    pr_auc = (
        average_precision_score(
            y_true,
            y_probability,
        )
    )

    mcc = matthews_corrcoef(
        y_true,
        y_pred,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
    )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print(
        "\nFINAL TEST METRICS"
    )

    print(
        "-" * 60
    )

    print(
        f"Accuracy:          "
        f"{accuracy:.4f}"
    )

    print(
        f"Balanced accuracy: "
        f"{balanced_accuracy:.4f}"
    )

    print(
        f"Precision:         "
        f"{precision:.4f}"
    )

    print(
        f"Recall:            "
        f"{recall:.4f}"
    )

    print(
        f"F1 score:          "
        f"{f1:.4f}"
    )

    print(
        f"ROC-AUC:           "
        f"{roc_auc:.4f}"
    )

    print(
        f"PR-AUC:            "
        f"{pr_auc:.4f}"
    )

    print(
        f"MCC:               "
        f"{mcc:.4f}"
    )

    print(
        "\nConfusion matrix:"
    )

    print(
        matrix
    )

    print(
        "\nClassification report:"
    )

    print(
        classification_report(
            y_true,
            y_pred,
            digits=4,
            zero_division=0,
        )
    )

    # --------------------------------------------------------
    # Save final test metrics
    # --------------------------------------------------------

    payload = {
        "evaluation": (
            "frozen_gene_held_out_test"
        ),

        "model": (
            "HistGradientBoostingClassifier"
        ),

        "target_description": (
            "ClinVar-derived pathogenicity "
            "proxy for computational "
            "variant-effect modeling"
        ),

        "test_rows": int(
            len(test)
        ),

        "held_out_genes": int(
            test[
                "gene_symbol"
            ].nunique()
        ),

        "class_distribution": {
            "benign_like": (
                benign_count
            ),

            "pathogenic_like": (
                pathogenic_count
            ),
        },

        "metrics": {
            "accuracy": float(
                accuracy
            ),

            "balanced_accuracy": float(
                balanced_accuracy
            ),

            "precision": float(
                precision
            ),

            "recall": float(
                recall
            ),

            "f1": float(
                f1
            ),

            "roc_auc": float(
                roc_auc
            ),

            "pr_auc": float(
                pr_auc
            ),

            "mcc": float(
                mcc
            ),

            "confusion_matrix": (
                matrix.tolist()
            ),
        },

        "scientific_scope": (
            "Research and educational "
            "computational prediction only. "
            "Not a clinical diagnostic result."
        ),
    }

    with open(
        FINAL_METRICS_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=4,
        )

    print(
        "\nFinal metrics artifact:"
    )

    print(
        FINAL_METRICS_PATH
    )

    print(
        "\nImportant:"
    )

    print(
        "These results represent performance "
        "on genes completely excluded from "
        "model training and validation."
    )

    print(
        "\n✅ Sprint 4 final held-out "
        "evaluation completed."
    )


if __name__ == "__main__":

    evaluate_final_model()