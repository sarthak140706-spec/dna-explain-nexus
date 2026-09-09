import json
import pickle
import sys

import pandas as pd

try:
    from .config import (
        PROJECT_ROOT,
        TRAIN_DATASET_PATH,
        VALIDATION_DATASET_PATH,
        TEST_DATASET_PATH,
    )

    from .features import (
        NUMERIC_FEATURE_COLUMNS,
        CATEGORICAL_FEATURE_COLUMNS,
    )

    from .predictor import (
        predict_variant,
        FEATURE_COLUMNS,
        MODEL_PATH,
    )

except ImportError:
    from config import (
        PROJECT_ROOT,
        TRAIN_DATASET_PATH,
        VALIDATION_DATASET_PATH,
        TEST_DATASET_PATH,
    )

    from features import (
        NUMERIC_FEATURE_COLUMNS,
        CATEGORICAL_FEATURE_COLUMNS,
    )

    from predictor import (
        predict_variant,
        FEATURE_COLUMNS,
        MODEL_PATH,
    )


# ============================================================
# Paths
# ============================================================

FINAL_METRICS_PATH = (
    PROJECT_ROOT
    / "backend"
    / "modeling"
    / "artifacts"
    / "final_test_metrics_v1.json"
)


# ============================================================
# Verification state
# ============================================================

passed_checks = 0
failed_checks = 0


def check(
    condition,
    name,
):
    global passed_checks
    global failed_checks

    if condition:
        print(
            f"[PASS] {name}"
        )
        passed_checks += 1

    else:
        print(
            f"[FAIL] {name}"
        )
        failed_checks += 1


# ============================================================
# Dataset verification
# ============================================================

def verify_datasets():

    print(
        "\n1. DATASET VERIFICATION"
    )

    print(
        "-" * 65
    )

    check(
        TRAIN_DATASET_PATH.exists(),
        "Training dataset exists",
    )

    check(
        VALIDATION_DATASET_PATH.exists(),
        "Validation dataset exists",
    )

    check(
        TEST_DATASET_PATH.exists(),
        "Test dataset exists",
    )

    train = pd.read_csv(
        TRAIN_DATASET_PATH,
        low_memory=False,
    )

    validation = pd.read_csv(
        VALIDATION_DATASET_PATH,
        low_memory=False,
    )

    test = pd.read_csv(
        TEST_DATASET_PATH,
        low_memory=False,
    )

    print(
        f"\nTrain rows:      "
        f"{len(train):,}"
    )

    print(
        f"Validation rows: "
        f"{len(validation):,}"
    )

    print(
        f"Test rows:       "
        f"{len(test):,}"
    )

    check(
        len(train) == 149677,
        "Frozen training row count",
    )

    check(
        len(validation) == 29640,
        "Frozen validation row count",
    )

    check(
        len(test) == 32029,
        "Frozen test row count",
    )

    total_rows = (
        len(train)
        + len(validation)
        + len(test)
    )

    check(
        total_rows == 211346,
        "All modeling variants accounted for",
    )

    # --------------------------------------------------------
    # Gene leakage
    # --------------------------------------------------------

    train_genes = set(
        train[
            "gene_symbol"
        ].astype(str)
    )

    validation_genes = set(
        validation[
            "gene_symbol"
        ].astype(str)
    )

    test_genes = set(
        test[
            "gene_symbol"
        ].astype(str)
    )

    check(
        len(
            train_genes
            & validation_genes
        ) == 0,
        "No train-validation gene leakage",
    )

    check(
        len(
            train_genes
            & test_genes
        ) == 0,
        "No train-test gene leakage",
    )

    check(
        len(
            validation_genes
            & test_genes
        ) == 0,
        "No validation-test gene leakage",
    )

    # --------------------------------------------------------
    # Variant leakage
    # --------------------------------------------------------

    train_variants = set(
        train[
            "variant_key"
        ].astype(str)
    )

    validation_variants = set(
        validation[
            "variant_key"
        ].astype(str)
    )

    test_variants = set(
        test[
            "variant_key"
        ].astype(str)
    )

    check(
        len(
            train_variants
            & validation_variants
        ) == 0,
        "No train-validation variant leakage",
    )

    check(
        len(
            train_variants
            & test_variants
        ) == 0,
        "No train-test variant leakage",
    )

    check(
        len(
            validation_variants
            & test_variants
        ) == 0,
        "No validation-test variant leakage",
    )

    # --------------------------------------------------------
    # Target verification
    # --------------------------------------------------------

    for name, dataframe in [
        ("Train", train),
        ("Validation", validation),
        ("Test", test),
    ]:

        targets = set(
            dataframe[
                "target_label"
            ]
            .astype(int)
            .unique()
        )

        check(
            targets == {0, 1},
            f"{name} contains both target classes",
        )


# ============================================================
# Feature verification
# ============================================================

def verify_features():

    print(
        "\n2. FEATURE VERIFICATION"
    )

    print(
        "-" * 65
    )

    print(
        f"\nFrozen predictive features: "
        f"{len(FEATURE_COLUMNS)}"
    )

    check(
        len(FEATURE_COLUMNS) == 28,
        "Selected model uses 28 predictive features",
    )

    check(
        "protein_position_log"
        not in FEATURE_COLUMNS,
        "Redundant protein_position_log excluded",
    )

    # --------------------------------------------------------
    # Leakage-prone fields
    # --------------------------------------------------------

    forbidden_features = {
        "gene_symbol",
        "gene_id",
        "hgnc_id",
        "source_clinical_significance",
        "source_clinsig_simple",
        "review_status",
        "number_submitters",
        "target_label",
        "target_name",
        "variation_id",
        "allele_id",
        "phenotype_list",
    }

    leaked_features = (
        forbidden_features
        & set(
            FEATURE_COLUMNS
        )
    )

    check(
        len(leaked_features) == 0,
        "No forbidden metadata used as predictive features",
    )

    if leaked_features:

        print(
            "Leaked fields:",
            leaked_features,
        )

    check(
        "gene_symbol"
        not in FEATURE_COLUMNS,
        "Gene identity is not a predictive feature",
    )

    check(
        "source_clinical_significance"
        not in FEATURE_COLUMNS,
        "ClinVar target source is not a predictive feature",
    )

    check(
        "review_status"
        not in FEATURE_COLUMNS,
        "ClinVar review metadata is not a predictive feature",
    )


# ============================================================
# Model artifact verification
# ============================================================

def verify_model_artifact():

    print(
        "\n3. MODEL ARTIFACT VERIFICATION"
    )

    print(
        "-" * 65
    )

    check(
        MODEL_PATH.exists(),
        "Selected model artifact exists",
    )

    if not MODEL_PATH.exists():
        return

    try:

        with open(
            MODEL_PATH,
            "rb",
        ) as file:

            model = pickle.load(
                file
            )

        check(
            model is not None,
            "Selected model artifact loads",
        )

        check(
            hasattr(
                model,
                "predict",
            ),
            "Model exposes predict()",
        )

        check(
            hasattr(
                model,
                "predict_proba",
            ),
            "Model exposes predict_proba()",
        )

        if hasattr(
            model,
            "named_steps",
        ):

            classifier = (
                model.named_steps.get(
                    "classifier"
                )
            )

            check(
                classifier is not None,
                "Classifier exists inside pipeline",
            )

            if classifier is not None:

                check(
                    classifier.__class__.__name__
                    ==
                    "HistGradientBoostingClassifier",
                    "Frozen model is HistGradientBoostingClassifier",
                )

    except Exception as error:

        check(
            False,
            "Selected model artifact loads",
        )

        print(
            f"Artifact error: {error}"
        )


# ============================================================
# Prediction verification
# ============================================================

def verify_prediction_engine():

    print(
        "\n4. PREDICTION ENGINE VERIFICATION"
    )

    print(
        "-" * 65
    )

    valid_variant = {
        "reference_allele": "G",
        "alternate_allele": "A",
        "reference_aa": "R",
        "alternate_aa": "H",
        "protein_position": 248,
    }

    try:

        result_1 = predict_variant(
            valid_variant
        )

        result_2 = predict_variant(
            valid_variant
        )

        check(
            isinstance(
                result_1,
                dict,
            ),
            "Prediction returns structured dictionary",
        )

        required_output_fields = {
            "predicted_class",
            "predicted_class_name",
            "model_score",
            "target_interpretation",
            "score_interpretation",
            "model_name",
            "model_version",
            "research_only",
        }

        check(
            required_output_fields.issubset(
                result_1.keys()
            ),
            "Prediction contains required output fields",
        )

        check(
            result_1[
                "predicted_class"
            ]
            in {0, 1},
            "Predicted class is valid",
        )

        check(
            result_1[
                "predicted_class_name"
            ]
            in {
                "benign_like",
                "pathogenic_like",
            },
            "Predicted class name is valid",
        )

        score = float(
            result_1[
                "model_score"
            ]
        )

        check(
            0.0 <= score <= 1.0,
            "Model score lies within [0, 1]",
        )

        check(
            result_1[
                "predicted_class"
            ]
            ==
            result_2[
                "predicted_class"
            ],
            "Prediction class is deterministic",
        )

        check(
            abs(
                float(
                    result_1[
                        "model_score"
                    ]
                )
                -
                float(
                    result_2[
                        "model_score"
                    ]
                )
            )
            < 1e-12,
            "Prediction score is deterministic",
        )

        check(
            result_1[
                "research_only"
            ]
            is True,
            "Research-only flag is present",
        )

        score_text = (
            result_1[
                "score_interpretation"
            ].lower()
        )

        check(
            "not calibrated confidence"
            in score_text,
            "Raw score is not mislabeled as confidence",
        )

        print(
            "\nSmoke-test prediction:"
        )

        print(
            f"Class: "
            f"{result_1['predicted_class_name']}"
        )

        print(
            f"Score: "
            f"{score:.6f}"
        )

    except Exception as error:

        check(
            False,
            "Valid prediction completes successfully",
        )

        print(
            f"Prediction error: {error}"
        )

    # --------------------------------------------------------
    # Invalid DNA input
    # --------------------------------------------------------

    invalid_dna = {
        "reference_allele": "G",
        "alternate_allele": "G",
        "reference_aa": "R",
        "alternate_aa": "H",
        "protein_position": 248,
    }

    try:

        predict_variant(
            invalid_dna
        )

        check(
            False,
            "Identical REF/ALT alleles rejected",
        )

    except ValueError:

        check(
            True,
            "Identical REF/ALT alleles rejected",
        )

    except Exception:

        check(
            False,
            "Identical REF/ALT alleles rejected",
        )

    # --------------------------------------------------------
    # Invalid amino-acid input
    # --------------------------------------------------------

    invalid_aa = {
        "reference_allele": "G",
        "alternate_allele": "A",
        "reference_aa": "R",
        "alternate_aa": "R",
        "protein_position": 248,
    }

    try:

        predict_variant(
            invalid_aa
        )

        check(
            False,
            "Identical amino acids rejected",
        )

    except ValueError:

        check(
            True,
            "Identical amino acids rejected",
        )

    except Exception:

        check(
            False,
            "Identical amino acids rejected",
        )

    # --------------------------------------------------------
    # Invalid protein position
    # --------------------------------------------------------

    invalid_position = {
        "reference_allele": "G",
        "alternate_allele": "A",
        "reference_aa": "R",
        "alternate_aa": "H",
        "protein_position": 0,
    }

    try:

        predict_variant(
            invalid_position
        )

        check(
            False,
            "Invalid protein position rejected",
        )

    except ValueError:

        check(
            True,
            "Invalid protein position rejected",
        )

    except Exception:

        check(
            False,
            "Invalid protein position rejected",
        )


# ============================================================
# Final metrics verification
# ============================================================

def verify_final_metrics():

    print(
        "\n5. FINAL TEST METRICS VERIFICATION"
    )

    print(
        "-" * 65
    )

    check(
        FINAL_METRICS_PATH.exists(),
        "Final test metrics artifact exists",
    )

    if not FINAL_METRICS_PATH.exists():
        return

    try:

        with open(
            FINAL_METRICS_PATH,
            "r",
            encoding="utf-8",
        ) as file:

            payload = json.load(
                file
            )

        check(
            payload.get(
                "evaluation"
            )
            ==
            "frozen_gene_held_out_test",
            "Metrics identify frozen held-out test evaluation",
        )

        check(
            payload.get(
                "test_rows"
            )
            == 32029,
            "Final metrics contain correct test row count",
        )

        check(
            payload.get(
                "held_out_genes"
            )
            == 2414,
            "Final metrics contain correct held-out gene count",
        )

        metrics = payload.get(
            "metrics",
            {}
        )

        required_metrics = {
            "accuracy",
            "balanced_accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "pr_auc",
            "mcc",
            "confusion_matrix",
        }

        check(
            required_metrics.issubset(
                metrics.keys()
            ),
            "All required final metrics are stored",
        )

        check(
            abs(
                metrics.get(
                    "balanced_accuracy",
                    0,
                )
                - 0.7032
            )
            < 0.0001,
            "Frozen balanced accuracy matches evaluation",
        )

        check(
            abs(
                metrics.get(
                    "roc_auc",
                    0,
                )
                - 0.7705
            )
            < 0.0001,
            "Frozen ROC-AUC matches evaluation",
        )

        check(
            abs(
                metrics.get(
                    "pr_auc",
                    0,
                )
                - 0.6629
            )
            < 0.0001,
            "Frozen PR-AUC matches evaluation",
        )

    except Exception as error:

        check(
            False,
            "Final metrics artifact can be parsed",
        )

        print(
            f"Metrics error: {error}"
        )


# ============================================================
# Main verification
# ============================================================

def main():

    print(
        "GeneMirror Sprint 4 Final Verification"
    )

    print(
        "=" * 65
    )

    verify_datasets()

    verify_features()

    verify_model_artifact()

    verify_prediction_engine()

    verify_final_metrics()

    print(
        "\n"
        + "=" * 65
    )

    print(
        "FINAL VERIFICATION SUMMARY"
    )

    print(
        "=" * 65
    )

    print(
        f"Passed checks: {passed_checks}"
    )

    print(
        f"Failed checks: {failed_checks}"
    )

    if failed_checks == 0:

        print(
            "\n✅ SPRINT 4 MODEL VERIFICATION PASSED"
        )

        print(
            "\nSelected model:"
        )

        print(
            "HistGradientBoostingClassifier"
        )

        print(
            "\nHeld-out test performance:"
        )

        print(
            "Balanced Accuracy: 0.7032"
        )

        print(
            "ROC-AUC:           0.7705"
        )

        print(
            "PR-AUC:            0.6629"
        )

        print(
            "F1:                0.6255"
        )

        print(
            "MCC:               0.3971"
        )

        print(
            "\nScientific interpretation:"
        )

        print(
            "ClinVar-derived pathogenicity proxy "
            "for computational variant-effect modeling."
        )

        print(
            "Research/education only; not a clinical "
            "diagnostic prediction."
        )

        return 0

    print(
        "\n❌ SPRINT 4 MODEL VERIFICATION FAILED"
    )

    print(
        "Resolve failed checks before freezing Sprint 4."
    )

    return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )