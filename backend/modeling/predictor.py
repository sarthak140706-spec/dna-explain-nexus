import pickle
from typing import Dict, Any

import pandas as pd

try:
    # Package import:
    # from backend.modeling.predictor import ...
    from .config import PROJECT_ROOT

    from .features import (
        create_features,
        NUMERIC_FEATURE_COLUMNS,
        CATEGORICAL_FEATURE_COLUMNS,
    )

except ImportError:
    # Direct execution:
    # python backend\modeling\predictor.py
    from config import PROJECT_ROOT

    from features import (
        create_features,
        NUMERIC_FEATURE_COLUMNS,
        CATEGORICAL_FEATURE_COLUMNS,
    )


# ============================================================
# Frozen selected model
# ============================================================

MODEL_PATH = (
    PROJECT_ROOT
    / "backend"
    / "modeling"
    / "artifacts"
    / "hist_gradient_boosting_v1.pkl"
)


# The selected model excluded protein_position_log
# because it duplicated the same positional information.

NUMERIC_FEATURES = [
    feature
    for feature in NUMERIC_FEATURE_COLUMNS
    if feature != "protein_position_log"
]

FEATURE_COLUMNS = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURE_COLUMNS
)


CLASS_NAMES = {
    0: "benign_like",
    1: "pathogenic_like",
}


# ============================================================
# Model loader
# ============================================================

def load_model():
    """
    Load the frozen Sprint 4 model.
    """

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            "GeneMirror model artifact not found:\n"
            f"{MODEL_PATH}"
        )

    with open(
        MODEL_PATH,
        "rb",
    ) as file:

        model = pickle.load(
            file
        )

    return model


# ============================================================
# Input validation
# ============================================================

def validate_variant_input(
    variant: Dict[str, Any],
):
    """
    Validate the minimum information required
    for Sprint 4 feature generation.
    """

    required_fields = [
        "reference_allele",
        "alternate_allele",
        "reference_aa",
        "alternate_aa",
        "protein_position",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in variant
        or variant[field] is None
    ]

    if missing_fields:

        raise ValueError(
            "Missing required variant fields:\n"
            + "\n".join(missing_fields)
        )

    # --------------------------------------------------------
    # DNA allele validation
    # --------------------------------------------------------

    valid_bases = {
        "A",
        "C",
        "G",
        "T",
    }

    reference_allele = str(
        variant[
            "reference_allele"
        ]
    ).upper()

    alternate_allele = str(
        variant[
            "alternate_allele"
        ]
    ).upper()

    if reference_allele not in valid_bases:

        raise ValueError(
            "reference_allele must be "
            "A, C, G, or T."
        )

    if alternate_allele not in valid_bases:

        raise ValueError(
            "alternate_allele must be "
            "A, C, G, or T."
        )

    if reference_allele == alternate_allele:

        raise ValueError(
            "Reference and alternate alleles "
            "must be different."
        )

    # --------------------------------------------------------
    # Amino-acid validation
    # --------------------------------------------------------

    valid_amino_acids = set(
        "ACDEFGHIKLMNPQRSTVWY"
    )

    reference_aa = str(
        variant[
            "reference_aa"
        ]
    ).upper()

    alternate_aa = str(
        variant[
            "alternate_aa"
        ]
    ).upper()

    if reference_aa not in valid_amino_acids:

        raise ValueError(
            "reference_aa must be a canonical "
            "one-letter amino-acid code."
        )

    if alternate_aa not in valid_amino_acids:

        raise ValueError(
            "alternate_aa must be a canonical "
            "one-letter amino-acid code."
        )

    if reference_aa == alternate_aa:

        raise ValueError(
            "Reference and alternate amino acids "
            "must be different for a missense variant."
        )

    # --------------------------------------------------------
    # Protein position validation
    # --------------------------------------------------------

    try:

        protein_position = int(
            variant[
                "protein_position"
            ]
        )

    except (TypeError, ValueError):

        raise ValueError(
            "protein_position must be "
            "a positive integer."
        )

    if protein_position <= 0:

        raise ValueError(
            "protein_position must be "
            "greater than zero."
        )


# ============================================================
# Normalize input
# ============================================================

def normalize_variant(
    variant: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Normalize user/backend variant input before
    feature engineering.
    """

    normalized = dict(
        variant
    )

    normalized[
        "reference_allele"
    ] = str(
        normalized[
            "reference_allele"
        ]
    ).upper()

    normalized[
        "alternate_allele"
    ] = str(
        normalized[
            "alternate_allele"
        ]
    ).upper()

    normalized[
        "reference_aa"
    ] = str(
        normalized[
            "reference_aa"
        ]
    ).upper()

    normalized[
        "alternate_aa"
    ] = str(
        normalized[
            "alternate_aa"
        ]
    ).upper()

    normalized[
        "protein_position"
    ] = int(
        normalized[
            "protein_position"
        ]
    )

    return normalized


# ============================================================
# Prediction engine
# ============================================================

class GeneMirrorPredictor:
    """
    Sprint 4 inference interface.

    Important:
    model_score is an uncalibrated model probability.

    It must NOT be presented as calibrated confidence.
    """

    def __init__(self):

        self.model = load_model()

    def predict(
        self,
        variant: Dict[str, Any],
    ) -> Dict[str, Any]:

        validate_variant_input(
            variant
        )

        normalized_variant = (
            normalize_variant(
                variant
            )
        )

        raw_dataframe = pd.DataFrame(
            [
                normalized_variant
            ]
        )

        feature_dataframe = (
            create_features(
                raw_dataframe
            )
        )

        missing_features = [
            feature
            for feature in FEATURE_COLUMNS
            if feature
            not in feature_dataframe.columns
        ]

        if missing_features:

            raise RuntimeError(
                "Feature engineering failed. "
                "Missing model features:\n"
                + "\n".join(
                    missing_features
                )
            )

        X = feature_dataframe[
            FEATURE_COLUMNS
        ]

        predicted_class = int(
            self.model.predict(
                X
            )[0]
        )

        model_score = float(
            self.model.predict_proba(
                X
            )[0, 1]
        )

        result = {
            "predicted_class": (
                predicted_class
            ),

            "predicted_class_name": (
                CLASS_NAMES[
                    predicted_class
                ]
            ),

            "model_score": (
                model_score
            ),

            "target_interpretation": (
                "ClinVar-derived pathogenicity "
                "proxy for computational "
                "variant-effect modeling"
            ),

            "score_interpretation": (
                "Uncalibrated model score. "
                "This is not calibrated confidence "
                "and is not a clinical probability."
            ),

            "model_name": (
                "HistGradientBoostingClassifier"
            ),

            "model_version": (
                "GeneMirror-v1-Sprint4"
            ),

            "research_only": True,
        }

        return result


# ============================================================
# Convenience function
# ============================================================

_predictor = None


def predict_variant(
    variant: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convenience interface for future FastAPI integration.
    """

    global _predictor

    if _predictor is None:

        _predictor = (
            GeneMirrorPredictor()
        )

    return _predictor.predict(
        variant
    )


# ============================================================
# Local smoke test
# ============================================================

if __name__ == "__main__":

    example_variant = {
        "reference_allele": "G",
        "alternate_allele": "A",
        "reference_aa": "R",
        "alternate_aa": "H",
        "protein_position": 248,
    }

    print(
        "GeneMirror Prediction Engine"
    )

    print(
        "=" * 65
    )

    print(
        "\nExample input:"
    )

    print(
        example_variant
    )

    result = predict_variant(
        example_variant
    )

    print(
        "\nPrediction:"
    )

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )

    print(
        "\n✅ Prediction engine smoke test passed."
    )