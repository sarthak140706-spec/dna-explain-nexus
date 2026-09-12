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

from backend.scientist.config import (
    RESEARCH_DISCLAIMER,
    SCIENTIST_CONTRACT_VERSION,
    SCIENTIST_VERSION,
    SUPPORTED_IMPACT_CLASSES,
)


# ============================================================
# Grounded evidence
# ============================================================

@dataclass
class GroundedEvidence:
    source: str
    category: str
    statement: str

    value: Optional[Any] = None

    supports: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# Variant information
# ============================================================

@dataclass
class ScientistVariant:
    gene_symbol: str

    chromosome: Optional[str] = None
    position: Optional[int] = None

    reference_allele: Optional[str] = None
    alternate_allele: Optional[str] = None

    dna_change: Optional[str] = None
    protein_change: Optional[str] = None

    protein_position: Optional[int] = None

    reference_amino_acid: Optional[str] = None
    alternate_amino_acid: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# Prediction information
# ============================================================

@dataclass
class ScientistPrediction:
    predicted_class: int
    predicted_class_name: str

    raw_model_score: float

    calibrated_probability: Optional[float] = None

    impact_class: Optional[str] = None

    confidence_score: Optional[float] = None
    uncertainty_score: Optional[float] = None

    confidence_band: Optional[str] = None

    model_name: Optional[str] = None
    model_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# XAI information
# ============================================================

@dataclass
class ScientistFeatureContribution:
    feature_name: str

    feature_value: Any

    contribution: float

    direction: str

    relative_local_influence_percent: Optional[
        float
    ] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# Protein context information
# ============================================================

@dataclass
class ScientistProteinContext:
    accession: Optional[str] = None

    protein_name: Optional[str] = None

    protein_length: Optional[int] = None

    sequence_window: Optional[str] = None

    window_start: Optional[int] = None
    window_end: Optional[int] = None

    overlapping_features: List[
        Dict[str, Any]
    ] = field(
        default_factory=list
    )

    nearby_features: List[
        Dict[str, Any]
    ] = field(
        default_factory=list
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# Complete Scientist input
# ============================================================

@dataclass
class ScientistInput:
    variant: ScientistVariant

    prediction: ScientistPrediction

    feature_contributions: List[
        ScientistFeatureContribution
    ] = field(
        default_factory=list
    )

    protein_context: Optional[
        ScientistProteinContext
    ] = None

    grounded_evidence: List[
        GroundedEvidence
    ] = field(
        default_factory=list
    )

    source_versions: Dict[
        str,
        str
    ] = field(
        default_factory=dict
    )

    research_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# Explanation sections
# ============================================================

@dataclass
class ScientistExplanationSections:
    overview: str

    prediction: str

    evidence: str

    protein_context: str

    limitations: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


# ============================================================
# Final Scientist output
# ============================================================

@dataclass
class ScientistOutput:
    variant: Dict[str, Any]

    sections: ScientistExplanationSections

    grounded_facts: List[
        Dict[str, Any]
    ] = field(
        default_factory=list
    )

    scientist_name: str = (
        "GeneMirror Scientist"
    )

    scientist_version: str = (
        SCIENTIST_VERSION
    )

    contract_version: str = (
        SCIENTIST_CONTRACT_VERSION
    )

    provider: Optional[str] = None

    language_model: Optional[str] = None

    research_only: bool = True

    disclaimer: str = (
        RESEARCH_DISCLAIMER
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# Input validation
# ============================================================

def validate_scientist_input(
    scientist_input: ScientistInput,
) -> None:

    variant = scientist_input.variant

    prediction = scientist_input.prediction

    if not variant.gene_symbol.strip():
        raise ValueError(
            "Gene symbol is required."
        )

    if prediction.predicted_class not in (
        0,
        1,
    ):
        raise ValueError(
            "Predicted class must be 0 or 1."
        )

    if not (
        0.0
        <= prediction.raw_model_score
        <= 1.0
    ):
        raise ValueError(
            "Raw model score must be "
            "between 0 and 1."
        )

    if (
        prediction.calibrated_probability
        is not None
    ):

        if not (
            0.0
            <= prediction.calibrated_probability
            <= 1.0
        ):
            raise ValueError(
                "Calibrated probability must "
                "be between 0 and 1."
            )

    if (
        prediction.confidence_score
        is not None
    ):

        if not (
            0.0
            <= prediction.confidence_score
            <= 1.0
        ):
            raise ValueError(
                "Confidence score must be "
                "between 0 and 1."
            )

    if (
        prediction.uncertainty_score
        is not None
    ):

        if not (
            0.0
            <= prediction.uncertainty_score
            <= 1.0
        ):
            raise ValueError(
                "Uncertainty score must be "
                "between 0 and 1."
            )

    if (
        prediction.impact_class
        is not None
        and prediction.impact_class
        not in SUPPORTED_IMPACT_CLASSES
    ):

        raise ValueError(
            "Impact class must be one of "
            f"{SUPPORTED_IMPACT_CLASSES}."
        )

    if scientist_input.research_only is not True:
        raise ValueError(
            "Scientist input must preserve "
            "research_only=True."
        )

    for contribution in (
        scientist_input.feature_contributions
    ):

        if contribution.direction not in (
            "supports_higher",
            "supports_lower",
            "neutral",
        ):

            raise ValueError(
                "Invalid feature contribution "
                "direction."
            )

        percent = (
            contribution
            .relative_local_influence_percent
        )

        if percent is not None:

            if not (
                0.0
                <= percent
                <= 100.0
            ):

                raise ValueError(
                    "Relative local influence "
                    "must be between 0 and 100."
                )


# ============================================================
# Output validation
# ============================================================

def validate_scientist_output(
    output: ScientistOutput,
) -> None:

    sections = output.sections

    section_values = (
        sections.overview,
        sections.prediction,
        sections.evidence,
        sections.protein_context,
        sections.limitations,
    )

    if any(
        not value.strip()
        for value in section_values
    ):
        raise ValueError(
            "All Scientist explanation "
            "sections must contain text."
        )

    if output.research_only is not True:
        raise ValueError(
            "Scientist output must preserve "
            "research_only=True."
        )

    if not output.disclaimer.strip():
        raise ValueError(
            "Scientist safety disclaimer "
            "is required."
        )