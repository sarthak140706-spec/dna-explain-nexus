from pathlib import Path
import json
import pickle

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
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
# Model artifact paths
# ============================================================

MODEL_DIR = (
    PROJECT_ROOT
    / "backend"
    / "modeling"
    / "artifacts"
)

BASELINE_MODEL_PATH = (
    MODEL_DIR
    / "baseline_logistic_v1.pkl"
)

BASELINE_METRICS_PATH = (
    MODEL_DIR
    / "baseline_logistic_metrics_v1.json"
)


# ============================================================
# Feature configuration
# ============================================================

FEATURE_COLUMNS = (
    NUMERIC_FEATURE_COLUMNS
    + CATEGORICAL_FEATURE_COLUMNS
)

TARGET_COLUMN = "target_label"


# ============================================================
# Data loading
# ============================================================

def load_split(path: Path) -> pd.DataFrame:
    """
    Load one frozen Sprint 4 split.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{path}"
        )

    dataframe = pd.read_csv(
        path,
        low_memory=False,
    )

    return dataframe


# ============================================================
# Dataset validation
# ============================================================

def validate_modeling_dataset(
    dataframe: pd.DataFrame,
    dataset_name: str,
):
    """
    Ensure required model features and targets exist.
    """

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
            f"{dataset_name} is missing columns:\n"
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
            f"{dataset_name} contains "
            f"{missing_features} missing feature values."
        )

    target_values = set(
        dataframe[
            TARGET_COLUMN
        ]
        .astype(int)
        .unique()
    )

    if target_values != {0, 1}:
        raise ValueError(
            f"{dataset_name} has unexpected targets: "
            f"{target_values}"
        )


# ============================================================
# Preprocessor
# ============================================================

def build_preprocessor():
    """
    Numeric:
        StandardScaler

    Categorical:
        OneHotEncoder

    Unknown categories in validation/test are ignored.
    """

    numeric_transformer = Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            )
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=True,
                ),
            )
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_transformer,
                NUMERIC_FEATURE_COLUMNS,
            ),
            (
                "categorical",
                categorical_transformer,
                CATEGORICAL_FEATURE_COLUMNS,
            ),
        ]
    )

    return preprocessor


# ============================================================
# Baseline model
# ============================================================

def build_baseline_model():
    """
    Logistic regression baseline.

    class_weight='balanced' compensates for the
    benign/pathogenic class imbalance without SMOTE.
    """

    preprocessor = build_preprocessor()

    classifier = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        solver="liblinear",
        random_state=42,
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
    """
    Evaluate the model on one split.
    """

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
        "rows": int(
            len(dataframe)
        ),
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

def save_model(
    model,
):
    """
    Save fitted baseline pipeline.
    """

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        BASELINE_MODEL_PATH,
        "wb",
    ) as file:
        pickle.dump(
            model,
            file,
        )


def save_metrics(
    metrics,
):
    """
    Save evaluation metrics as JSON.
    """

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        BASELINE_METRICS_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            indent=4,
        )


# ============================================================
# Training pipeline
# ============================================================

def train_baseline():

    print(
        "GeneMirror Baseline Model"
    )

    print(
        "=" * 65
    )

    print(
        "\nModel:"
    )

    print(
        "Logistic Regression"
    )

    print(
        "\nTraining dataset:"
    )

    print(
        TRAIN_DATASET_PATH
    )

    print(
        "\nValidation dataset:"
    )

    print(
        VALIDATION_DATASET_PATH
    )

    train = load_split(
        TRAIN_DATASET_PATH
    )

    validation = load_split(
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

    validate_modeling_dataset(
        train,
        "train",
    )

    validate_modeling_dataset(
        validation,
        "validation",
    )

    X_train = train[
        FEATURE_COLUMNS
    ]

    y_train = train[
        TARGET_COLUMN
    ].astype(int)

    print(
        "\nTraining baseline model..."
    )

    model = (
        build_baseline_model()
    )

    model.fit(
        X_train,
        y_train,
    )

    print(
        "Training completed."
    )

    # --------------------------------------------------------
    # Validation only
    #
    # Test set remains untouched until the main model
    # has been selected.
    # --------------------------------------------------------

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
        {
            "model": (
                "LogisticRegression"
            ),
            "features": (
                FEATURE_COLUMNS
            ),
            "validation": (
                validation_metrics
            ),
        }
    )

    print(
        "\nArtifacts"
    )

    print(
        "-" * 60
    )

    print(
        f"Model:\n"
        f"{BASELINE_MODEL_PATH}"
    )

    print(
        f"\nMetrics:\n"
        f"{BASELINE_METRICS_PATH}"
    )

    print(
        "\nImportant:"
    )

    print(
        "The test dataset was NOT used "
        "during baseline training or selection."
    )

    print(
        "\n✅ Sprint 4 baseline model "
        "training completed."
    )


if __name__ == "__main__":

    train_baseline()