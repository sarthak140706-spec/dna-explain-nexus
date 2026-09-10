import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd


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
    EXPLANATION_VERSION,
    MODEL_ARTIFACT_PATH,
    MODEL_NAME,
    MODEL_VERSION,
    TARGET_INTERPRETATION,
)

from backend.explainability.contracts import (
    FeatureContribution,
    VariantExplanation,
    validate_explanation_contract,
)

from backend.modeling.config import (
    VALIDATION_DATASET_PATH,
)

from backend.modeling.features import (
    create_features,
    NUMERIC_FEATURE_COLUMNS,
    CATEGORICAL_FEATURE_COLUMNS,
)

from backend.modeling.predictor import (
    FEATURE_COLUMNS,
    predict_variant,
    validate_variant_input,
)


# ============================================================
# Configuration
# ============================================================

LOCAL_EXPLANATION_PATH = (
    ARTIFACTS_DIR
    / "local_explanation_example_v1.json"
)

NEUTRAL_THRESHOLD = 1e-6

TOP_FEATURE_COUNT = 10


# ============================================================
# Frozen model
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

        model = pickle.load(
            file
        )

    return model


# ============================================================
# Validation reference values
# ============================================================

def build_reference_profile():

    if not VALIDATION_DATASET_PATH.exists():

        raise FileNotFoundError(
            f"Validation dataset not found: "
            f"{VALIDATION_DATASET_PATH}"
        )

    validation = pd.read_csv(
        VALIDATION_DATASET_PATH,
        low_memory=False,
    )

    missing_features = [
        feature
        for feature in FEATURE_COLUMNS
        if feature not in validation.columns
    ]

    if missing_features:

        raise ValueError(
            "Validation dataset is missing "
            f"predictive features: {missing_features}"
        )

    reference_values = {}

    # --------------------------------------------------------
    # Numeric features
    # --------------------------------------------------------

    for feature in NUMERIC_FEATURE_COLUMNS:

        if feature not in FEATURE_COLUMNS:
            continue

        values = pd.to_numeric(
            validation[feature],
            errors="coerce",
        )

        median_value = values.median()

        if pd.isna(
            median_value
        ):

            raise ValueError(
                f"Unable to calculate median "
                f"for feature: {feature}"
            )

        reference_values[
            feature
        ] = float(
            median_value
        )

    # --------------------------------------------------------
    # Categorical features
    # --------------------------------------------------------

    for feature in CATEGORICAL_FEATURE_COLUMNS:

        if feature not in FEATURE_COLUMNS:
            continue

        mode_values = (
            validation[
                feature
            ]
            .dropna()
            .astype(str)
            .mode()
        )

        if mode_values.empty:

            raise ValueError(
                f"Unable to calculate mode "
                f"for feature: {feature}"
            )

        reference_values[
            feature
        ] = str(
            mode_values.iloc[0]
        )

    missing_reference = (
        set(FEATURE_COLUMNS)
        - set(reference_values)
    )

    if missing_reference:

        raise ValueError(
            "Reference profile does not contain "
            f"all model features: "
            f"{sorted(missing_reference)}"
        )

    return reference_values


# ============================================================
# Convert input variant into model features
# ============================================================

def prepare_variant_features(
    variant,
):

    required = {
        "reference_allele",
        "alternate_allele",
        "reference_aa",
        "alternate_aa",
        "protein_position",
    }

    missing = (
        required
        - set(variant.keys())
    )

    if missing:

        raise ValueError(
            f"Missing required variant fields: "
            f"{sorted(missing)}"
        )

    reference_allele = str(
        variant[
            "reference_allele"
        ]
    ).strip().upper()

    alternate_allele = str(
        variant[
            "alternate_allele"
        ]
    ).strip().upper()

    reference_aa = str(
        variant[
            "reference_aa"
        ]
    ).strip().upper()

    alternate_aa = str(
        variant[
            "alternate_aa"
        ]
    ).strip().upper()

    protein_position = variant[
        "protein_position"
    ]

    validate_variant_input(
    {
        "reference_allele": reference_allele,
        "alternate_allele": alternate_allele,
        "reference_aa": reference_aa,
        "alternate_aa": alternate_aa,
        "protein_position": protein_position,
    }
)

    dataframe = pd.DataFrame(
        [
            {
                "reference_allele": (
                    reference_allele
                ),
                "alternate_allele": (
                    alternate_allele
                ),
                "reference_aa": (
                    reference_aa
                ),
                "alternate_aa": (
                    alternate_aa
                ),
                "protein_position": int(
                    protein_position
                ),
            }
        ]
    )

    featured = create_features(
        dataframe
    )

    missing_features = [
        feature
        for feature in FEATURE_COLUMNS
        if feature not in featured.columns
    ]

    if missing_features:

        raise ValueError(
            "Feature engineering did not generate "
            f"required model features: "
            f"{missing_features}"
        )

    return featured[
        FEATURE_COLUMNS
    ].copy()


# ============================================================
# Score helper
# ============================================================

def predict_score(
    model,
    feature_dataframe,
):

    probabilities = model.predict_proba(
        feature_dataframe
    )

    score = float(
        probabilities[0][1]
    )

    if not (
        0.0 <= score <= 1.0
    ):

        raise ValueError(
            "Model returned score outside [0, 1]."
        )

    return score


# ============================================================
# Contribution direction
# ============================================================

def contribution_direction(
    contribution,
):

    if contribution > NEUTRAL_THRESHOLD:

        return (
            "supports_higher_impact"
        )

    if contribution < -NEUTRAL_THRESHOLD:

        return (
            "supports_lower_impact"
        )

    return "neutral"


# ============================================================
# Local explanation
# ============================================================

def explain_variant(
    variant,
    model=None,
    reference_values=None,
):

    if model is None:

        model = load_model()

    if reference_values is None:

        reference_values = (
            build_reference_profile()
        )

    # --------------------------------------------------------
    # Frozen Sprint 4 prediction
    # --------------------------------------------------------

    prediction = predict_variant(
        variant
    )

    # --------------------------------------------------------
    # Feature representation
    # --------------------------------------------------------

    features = prepare_variant_features(
        variant
    )

    original_score = predict_score(
        model,
        features,
    )

    predictor_score = float(
        prediction[
            "model_score"
        ]
    )

    if abs(
        original_score
        - predictor_score
    ) > 1e-10:

        raise ValueError(
            "Local explainer score does not match "
            "the frozen prediction engine."
        )

    contributions = []

    # --------------------------------------------------------
    # One-feature-at-a-time perturbation
    # --------------------------------------------------------

    for feature in FEATURE_COLUMNS:

        perturbed = features.copy()

        original_value = (
            features.iloc[0][
                feature
            ]
        )

        reference_value = (
            reference_values[
                feature
            ]
        )

        perturbed.loc[
            perturbed.index[0],
            feature,
        ] = reference_value

        perturbed_score = predict_score(
            model,
            perturbed,
        )

        contribution = (
            original_score
            - perturbed_score
        )

        direction = (
            contribution_direction(
                contribution
            )
        )

        contributions.append(
            FeatureContribution(
                feature_name=feature,
                feature_value=(
                    original_value.item()
                    if isinstance(
                        original_value,
                        np.generic,
                    )
                    else original_value
                ),
                contribution=float(
                    contribution
                ),
                direction=direction,
                importance=abs(
                    float(
                        contribution
                    )
                ),
            )
        )

    # --------------------------------------------------------
    # Rank by absolute local influence
    # --------------------------------------------------------

    ranked = sorted(
        contributions,
        key=lambda item: (
            item.importance
            if item.importance is not None
            else 0.0
        ),
        reverse=True,
    )

    top_features = ranked[
        :TOP_FEATURE_COUNT
    ]

    supporting = [
        item.feature_name
        for item in top_features
        if item.direction
        ==
        "supports_higher_impact"
    ]

    opposing = [
        item.feature_name
        for item in top_features
        if item.direction
        ==
        "supports_lower_impact"
    ]

    explanation = VariantExplanation(
        variant={
            "reference_allele": str(
                variant[
                    "reference_allele"
                ]
            ).upper(),
            "alternate_allele": str(
                variant[
                    "alternate_allele"
                ]
            ).upper(),
            "reference_aa": str(
                variant[
                    "reference_aa"
                ]
            ).upper(),
            "alternate_aa": str(
                variant[
                    "alternate_aa"
                ]
            ).upper(),
            "protein_position": int(
                variant[
                    "protein_position"
                ]
            ),
        },
        predicted_class=int(
            prediction[
                "predicted_class"
            ]
        ),
        predicted_class_name=(
            prediction[
                "predicted_class_name"
            ]
        ),
        raw_model_score=float(
            original_score
        ),
        feature_contributions=(
            ranked
        ),
        top_supporting_features=(
            supporting
        ),
        top_opposing_features=(
            opposing
        ),
    )

    validate_explanation_contract(
        explanation
    )

    return explanation


# ============================================================
# Save example explanation
# ============================================================

def save_explanation(
    explanation,
):

    payload = explanation.to_dict()

    payload[
        "local_explanation_method"
    ] = (
        "single-feature reference perturbation"
    )

    payload[
        "reference_dataset"
    ] = (
        "gene-held-out validation split"
    )

    payload[
        "test_set_used"
    ] = False

    payload[
        "explanation_scope"
    ] = (
        "Model-behavior explanation only. "
        "Feature contributions represent changes "
        "in the model score when individual "
        "features are replaced by validation-set "
        "reference values. They must not be "
        "interpreted as causal biological effects."
    )

    with open(
        LOCAL_EXPLANATION_PATH,
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
# Smoke test
# ============================================================

def main():

    print(
        "GeneMirror Sprint 5 "
        "Local Variant Explainability"
    )

    print(
        "=" * 65
    )

    variant = {
        "reference_allele": "G",
        "alternate_allele": "A",
        "reference_aa": "R",
        "alternate_aa": "H",
        "protein_position": 248,
    }

    print(
        "\nLoading frozen model..."
    )

    model = load_model()

    print(
        "Model loaded successfully."
    )

    print(
        "\nBuilding validation "
        "reference profile..."
    )

    reference_values = (
        build_reference_profile()
    )

    print(
        f"Reference features: "
        f"{len(reference_values)}"
    )

    print(
        "\nExplaining example variant..."
    )

    explanation = explain_variant(
        variant=variant,
        model=model,
        reference_values=(
            reference_values
        ),
    )

    payload = save_explanation(
        explanation
    )

    print(
        f"\nPredicted class: "
        f"{explanation.predicted_class_name}"
    )

    print(
        f"Raw model score: "
        f"{explanation.raw_model_score:.6f}"
    )

    print(
        "\nTop 10 local feature contributions"
    )

    print(
        "-" * 80
    )

    print(
        f"{'Rank':<6}"
        f"{'Feature':<32}"
        f"{'Contribution':>14} "
        f"{'Direction'}"
    )

    print(
        "-" * 80
    )

    for rank, item in enumerate(
        explanation.feature_contributions[
            :TOP_FEATURE_COUNT
        ],
        start=1,
    ):

        print(
            f"{rank:<6}"
            f"{item.feature_name:<32}"
            f"{item.contribution:>14.6f} "
            f"{item.direction}"
        )

    print(
        "\nTop supporting features:"
    )

    if explanation.top_supporting_features:

        for feature in (
            explanation.top_supporting_features
        ):

            print(
                f"  + {feature}"
            )

    else:

        print(
            "  None"
        )

    print(
        "\nTop opposing features:"
    )

    if explanation.top_opposing_features:

        for feature in (
            explanation.top_opposing_features
        ):

            print(
                f"  - {feature}"
            )

    else:

        print(
            "  None"
        )

    print(
        "\nContribution count:",
        len(
            explanation.feature_contributions
        ),
    )

    print(
        "Test set used:",
        payload[
            "test_set_used"
        ],
    )

    print(
        "\nOutput:"
    )

    print(
        LOCAL_EXPLANATION_PATH
    )

    print(
        "\nImportant:"
    )

    print(
        "Contributions describe model behavior, "
        "not causal biological effects."
    )

    print(
        "\n✅ Sprint 5 local variant "
        "explainability completed."
    )


if __name__ == "__main__":
    main()