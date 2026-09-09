from pathlib import Path
import json
import pickle

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingClassifier

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
    TRAIN_DATASET_PATH,
    VALIDATION_DATASET_PATH,
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

MAIN_METRICS_PATH = (
    MODEL_DIR
    / "hist_gradient_boosting_metrics_v1.json"
)


# ============================================================
# Feature configuration
# ============================================================

# Keep only one representation of protein position.
# protein_position is retained.
# protein_position_log is removed because it duplicates
# the same underlying information.

MAIN_NUMERIC_FEATURES = [
    feature
    for feature in NUMERIC_FEATURE_COLUMNS
    if feature != "protein_position_log"
]

FEATURE_COLUMNS = (
    MAIN_NUMERIC_FEATURES
    + CATEGORICAL_FEATURE_COLUMNS
)

TARGET_COLUMN = "target_label"


# ============================================================
# Load dataset
# ============================================================

def load_dataset(path: Path) -> pd.DataFrame:

    if not path.exists():

        raise FileNotFoundError(
            f"Dataset not found:\n{path}"
        )

    return pd.read_csv(
        path,
        low_memory=False,
    )


# ============================================================
# Validate dataset
# ============================================================

def validate_dataset(
    dataframe: pd.DataFrame,
    dataset_name: str,
):

    required_columns = (
        FEATURE_COLUMNS
        + [TARGET_COLUMN]
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:

        raise KeyError(
            f"{dataset_name} missing columns:\n"
            + "\n".join(missing_columns)
        )

    missing_values = int(
        dataframe[
            FEATURE_COLUMNS
        ]
        .isna()
        .sum()
        .sum()
    )

    if missing_values != 0:

        raise ValueError(
            f"{dataset_name} contains "
            f"{missing_values} missing "
            "feature values."
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
            f"{dataset_name} contains "
            f"unexpected target classes: "
            f"{targets}"
        )


# ============================================================
# Preprocessing
# ============================================================

def build_preprocessor():
    """
    Numeric features:
        passed directly

    Categorical features:
        dense one-hot encoding

    Dense output is used because
    HistGradientBoostingClassifier expects dense input.
    """

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                "passthrough",
                MAIN_NUMERIC_FEATURES,
            ),

            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                CATEGORICAL_FEATURE_COLUMNS,
            ),
        ]
    )

    return preprocessor


# ============================================================
# Main model
# ============================================================

def build_main_model():

    preprocessor = (
        build_preprocessor()
    )

    classifier = (
        HistGradientBoostingClassifier(
            learning_rate=0.08,
            max_iter=300,
            max_leaf_nodes=31,
            max_depth=None,
            min_samples_leaf=30,
            l2_regularization=1.0,
            class_weight="balanced",
            early_stopping=True,
            validation_fraction=0.10,
            n_iter_no_change=20,
            random_state=42,
        )
    )

    model = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),

            (
                "classifier",
                classifier,
            ),
        ]
    )

    return model


# ============================================================
# Evaluation
# ============================================================

def evaluate_model(
    model,
    dataframe: pd.DataFrame,
    dataset_name: str,
):

    X = dataframe[
        FEATURE_COLUMNS
    ]

    y_true = dataframe[
        TARGET_COLUMN
    ].astype(int)

    y_pred = model.predict(
        X
    )

    y_probability = (
        model.predict_proba(
            X
        )[:, 1]
    )

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

    pr_auc = average_precision_score(
        y_true,
        y_probability,
    )

    mcc = matthews_corrcoef(
        y_true,
        y_pred,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
    )

    metrics = {
        "dataset": dataset_name,
        "rows": int(len(dataframe)),
        "accuracy": float(accuracy),
        "balanced_accuracy": float(
            balanced_accuracy
        ),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "mcc": float(mcc),
        "confusion_matrix": (
            matrix.tolist()
        ),
    }

    print(
        f"\n{dataset_name.upper()} METRICS"
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

    return metrics


# ============================================================
# Save artifacts
# ============================================================

def save_model(model):

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        MAIN_MODEL_PATH,
        "wb",
    ) as file:

        pickle.dump(
            model,
            file,
        )


def save_metrics(
    metrics,
    model,
):

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    classifier = model.named_steps[
        "classifier"
    ]

    payload = {
        "model": (
            "HistGradientBoostingClassifier"
        ),

        "target_description": (
            "ClinVar-derived pathogenicity "
            "proxy for computational "
            "variant-effect modeling"
        ),

        "model_parameters": {
            "learning_rate": 0.08,
            "max_iter": 300,
            "max_leaf_nodes": 31,
            "min_samples_leaf": 30,
            "l2_regularization": 1.0,
            "class_weight": "balanced",
            "random_state": 42,
        },

        "predictive_features": (
            FEATURE_COLUMNS
        ),

        "removed_redundant_feature": (
            "protein_position_log"
        ),

        "iterations_used": int(
            classifier.n_iter_
        ),

        "validation": metrics,
    }

    with open(
        MAIN_METRICS_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=4,
        )


# ============================================================
# Training pipeline
# ============================================================

def train_main_model():

    print(
        "GeneMirror Main Model Candidate"
    )

    print(
        "=" * 65
    )

    print(
        "\nModel:"
    )

    print(
        "HistGradientBoostingClassifier"
    )

    train = load_dataset(
        TRAIN_DATASET_PATH
    )

    validation = load_dataset(
        VALIDATION_DATASET_PATH
    )

    print(
        f"\nTraining rows: "
        f"{len(train):,}"
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
        "\nRedundant feature excluded:"
    )

    print(
        "protein_position_log"
    )

    validate_dataset(
        train,
        "train",
    )

    validate_dataset(
        validation,
        "validation",
    )

    X_train = train[
        FEATURE_COLUMNS
    ]

    y_train = train[
        TARGET_COLUMN
    ].astype(int)

    model = build_main_model()

    print(
        "\nTraining HistGradientBoosting..."
    )

    model.fit(
        X_train,
        y_train,
    )

    classifier = model.named_steps[
        "classifier"
    ]

    print(
        "Training completed."
    )

    print(
        f"Boosting iterations used: "
        f"{classifier.n_iter_}"
    )

    validation_metrics = (
        evaluate_model(
            model,
            validation,
            "validation",
        )
    )

    save_model(
        model
    )

    save_metrics(
        validation_metrics,
        model,
    )

    print(
        "\nArtifacts"
    )

    print(
        "-" * 60
    )

    print(
        f"Model:\n"
        f"{MAIN_MODEL_PATH}"
    )

    print(
        f"\nMetrics:\n"
        f"{MAIN_METRICS_PATH}"
    )

    print(
        "\nImportant:"
    )

    print(
        "The frozen test dataset has "
        "NOT been evaluated."
    )

    print(
        "\n✅ Main model candidate "
        "training completed."
    )


if __name__ == "__main__":

    train_main_model()