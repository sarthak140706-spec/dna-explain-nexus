from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import (
    Any,
    Dict,
    List,
    Optional,
)

try:
    from .config import (
        EXPLANATION_VERSION,
        MODEL_NAME,
        MODEL_VERSION,
        RAW_SCORE_INTERPRETATION,
        RESEARCH_DISCLAIMER,
        TARGET_INTERPRETATION,
    )

except ImportError:
    from config import (
        EXPLANATION_VERSION,
        MODEL_NAME,
        MODEL_VERSION,
        RAW_SCORE_INTERPRETATION,
        RESEARCH_DISCLAIMER,
        TARGET_INTERPRETATION,
    )


# ============================================================
# Individual feature contribution
# ============================================================

@dataclass
class FeatureContribution:

    feature_name: str

    feature_value: Any

    contribution: float

    direction: str

    importance: Optional[float] = None


# ============================================================
# Prediction explanation contract
# ============================================================

@dataclass
class VariantExplanation:

    # --------------------------------------------------------
    # Variant
    # --------------------------------------------------------

    variant: Dict[str, Any]

    # --------------------------------------------------------
    # Frozen Sprint 4 prediction
    # --------------------------------------------------------

    predicted_class: int

    predicted_class_name: str

    raw_model_score: float

    # --------------------------------------------------------
    # Explainability
    # --------------------------------------------------------

    feature_contributions: List[
        FeatureContribution
    ] = field(
        default_factory=list
    )

    top_supporting_features: List[str] = field(
        default_factory=list
    )

    top_opposing_features: List[str] = field(
        default_factory=list
    )

    # --------------------------------------------------------
    # Calibration
    #
    # These remain empty until calibration is implemented.
    # --------------------------------------------------------

    calibrated_probability: Optional[float] = None

    confidence_score: Optional[float] = None

    uncertainty_score: Optional[float] = None

    impact_class: Optional[str] = None

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    model_name: str = MODEL_NAME

    model_version: str = MODEL_VERSION

    explanation_version: str = EXPLANATION_VERSION

    target_interpretation: str = TARGET_INTERPRETATION

    raw_score_interpretation: str = (
        RAW_SCORE_INTERPRETATION
    )

    research_only: bool = True

    disclaimer: str = RESEARCH_DISCLAIMER

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return asdict(
            self
        )


# ============================================================
# Contract validation
# ============================================================

def validate_explanation_contract(
    explanation: VariantExplanation,
) -> None:

    if explanation.predicted_class not in {
        0,
        1,
    }:
        raise ValueError(
            "predicted_class must be 0 or 1."
        )

    if explanation.predicted_class_name not in {
        "benign_like",
        "pathogenic_like",
    }:
        raise ValueError(
            "Invalid predicted_class_name."
        )

    if not (
        0.0
        <= explanation.raw_model_score
        <= 1.0
    ):
        raise ValueError(
            "raw_model_score must lie within [0, 1]."
        )

    for contribution in (
        explanation.feature_contributions
    ):

        if contribution.direction not in {
            "supports_higher_impact",
            "supports_lower_impact",
            "neutral",
        }:
            raise ValueError(
                "Invalid feature contribution direction."
            )

    if (
        explanation.calibrated_probability
        is not None
    ):

        if not (
            0.0
            <= explanation.calibrated_probability
            <= 1.0
        ):
            raise ValueError(
                "calibrated_probability must lie "
                "within [0, 1]."
            )

    if (
        explanation.confidence_score
        is not None
    ):

        if not (
            0.0
            <= explanation.confidence_score
            <= 1.0
        ):
            raise ValueError(
                "confidence_score must lie "
                "within [0, 1]."
            )

    if (
        explanation.uncertainty_score
        is not None
    ):

        if not (
            0.0
            <= explanation.uncertainty_score
            <= 1.0
        ):
            raise ValueError(
                "uncertainty_score must lie "
                "within [0, 1]."
            )

    if explanation.impact_class is not None:

        if explanation.impact_class not in {
            "LOW",
            "MODERATE",
            "HIGH",
        }:
            raise ValueError(
                "impact_class must be LOW, "
                "MODERATE, HIGH, or None."
            )


# ============================================================
# Smoke test
# ============================================================

def main():

    print(
        "GeneMirror Sprint 5 "
        "Explanation Contract"
    )

    print(
        "=" * 60
    )

    example = VariantExplanation(
        variant={
            "reference_allele": "G",
            "alternate_allele": "A",
            "reference_aa": "R",
            "alternate_aa": "H",
            "protein_position": 248,
        },
        predicted_class=0,
        predicted_class_name="benign_like",
        raw_model_score=0.3944095695196884,
    )

    validate_explanation_contract(
        example
    )

    payload = example.to_dict()

    print(
        f"Model: "
        f"{payload['model_name']}"
    )

    print(
        f"Model version: "
        f"{payload['model_version']}"
    )

    print(
        f"Explanation version: "
        f"{payload['explanation_version']}"
    )

    print(
        f"Raw model score: "
        f"{payload['raw_model_score']:.6f}"
    )

    print(
        "\nCalibration fields:"
    )

    print(
        "calibrated_probability:",
        payload[
            "calibrated_probability"
        ],
    )

    print(
        "confidence_score:",
        payload[
            "confidence_score"
        ],
    )

    print(
        "uncertainty_score:",
        payload[
            "uncertainty_score"
        ],
    )

    print(
        "impact_class:",
        payload[
            "impact_class"
        ],
    )

    print(
        "\nResearch only:",
        payload[
            "research_only"
        ],
    )

    print(
        "\n✅ Sprint 5 explanation "
        "contract smoke test passed."
    )


if __name__ == "__main__":

    main()