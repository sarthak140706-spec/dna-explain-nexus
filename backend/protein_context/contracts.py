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


from backend.protein_context.config import (
    PROTEIN_CONTEXT_INTERPRETATION,
    PROTEIN_CONTEXT_VERSION,
    PROTEIN_VISUALIZATION_VERSION,
    RESEARCH_DISCLAIMER,
)


# ============================================================
# Protein identity
# ============================================================

@dataclass
class ProteinIdentity:

    accession: str

    gene_symbol: str

    protein_name: str

    organism: str

    sequence_length: int

    reviewed: bool

    entry_name: Optional[str] = None

    source: str = "UniProtKB"


# ============================================================
# Protein feature
# ============================================================

@dataclass
class ProteinFeature:

    feature_type: str

    start: int

    end: int

    description: Optional[str] = None

    feature_id: Optional[str] = None

    evidence: List[str] = field(
        default_factory=list
    )

    distance_to_variant: Optional[int] = None

    overlaps_variant: bool = False


# ============================================================
# Sequence context
# ============================================================

@dataclass
class SequenceContext:

    protein_position: int

    reference_amino_acid: str

    sequence_reference_amino_acid: str

    position_matches_reference: bool

    window_start: int

    window_end: int

    sequence_window: str

    variant_index_in_window: int

    protein_length: int


# ============================================================
# Visualization marker
# ============================================================

@dataclass
class VariantMarker:

    position: int

    reference_amino_acid: str

    alternate_amino_acid: str

    label: str


# ============================================================
# Visualization track
# ============================================================

@dataclass
class VisualizationTrack:

    track_type: str

    label: str

    features: List[Dict[str, Any]] = field(
        default_factory=list
    )


# ============================================================
# Complete protein-context response
# ============================================================

@dataclass
class ProteinContextResult:

    protein: ProteinIdentity

    variant: Dict[str, Any]

    sequence_context: SequenceContext

    overlapping_features: List[
        ProteinFeature
    ] = field(
        default_factory=list
    )

    nearby_features: List[
        ProteinFeature
    ] = field(
        default_factory=list
    )

    visualization_tracks: List[
        VisualizationTrack
    ] = field(
        default_factory=list
    )

    variant_marker: Optional[
        VariantMarker
    ] = None

    protein_context_version: str = (
        PROTEIN_CONTEXT_VERSION
    )

    visualization_version: str = (
        PROTEIN_VISUALIZATION_VERSION
    )

    interpretation: str = (
        PROTEIN_CONTEXT_INTERPRETATION
    )

    research_only: bool = True

    disclaimer: str = (
        RESEARCH_DISCLAIMER
    )

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return asdict(
            self
        )


# ============================================================
# Contract validation
# ============================================================

def validate_protein_context_contract(
    result: ProteinContextResult,
) -> None:

    if not isinstance(
        result,
        ProteinContextResult,
    ):

        raise TypeError(
            "Result must be a "
            "ProteinContextResult."
        )

    protein = result.protein

    if not protein.accession:

        raise ValueError(
            "Protein accession is required."
        )

    if not protein.gene_symbol:

        raise ValueError(
            "Gene symbol is required."
        )

    if (
        protein.sequence_length
        <= 0
    ):

        raise ValueError(
            "Protein sequence length "
            "must be positive."
        )

    sequence_context = (
        result.sequence_context
    )

    if (
        sequence_context.protein_position
        <= 0
    ):

        raise ValueError(
            "Protein position must "
            "be positive."
        )

    if (
        sequence_context.window_start
        <= 0
    ):

        raise ValueError(
            "Sequence window start "
            "must be positive."
        )

    if (
        sequence_context.window_end
        < sequence_context.window_start
    ):

        raise ValueError(
            "Sequence window boundaries "
            "are invalid."
        )

    if (
        sequence_context.window_end
        > protein.sequence_length
    ):

        raise ValueError(
            "Sequence window exceeds "
            "protein length."
        )

    if not (
        0
        <= sequence_context.variant_index_in_window
        < len(
            sequence_context.sequence_window
        )
    ):

        raise ValueError(
            "Variant index is outside "
            "the sequence window."
        )

    if (
        sequence_context.sequence_reference_amino_acid
        not in {
            "A",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "K",
            "L",
            "M",
            "N",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "V",
            "W",
            "Y",
        }
    ):

        raise ValueError(
            "Sequence reference amino acid "
            "is not canonical."
        )

    for feature in (
        result.overlapping_features
        + result.nearby_features
    ):

        if (
            feature.start
            <= 0
        ):

            raise ValueError(
                "Protein feature start "
                "must be positive."
            )

        if (
            feature.end
            < feature.start
        ):

            raise ValueError(
                "Protein feature boundaries "
                "are invalid."
            )

        if (
            feature.end
            > protein.sequence_length
        ):

            raise ValueError(
                "Protein feature exceeds "
                "protein sequence length."
            )

    if (
        result.variant_marker
        is not None
    ):

        marker = (
            result.variant_marker
        )

        if not (
            1
            <= marker.position
            <= protein.sequence_length
        ):

            raise ValueError(
                "Variant visualization marker "
                "is outside the protein."
            )

    if (
        result.research_only
        is not True
    ):

        raise ValueError(
            "Protein context result must "
            "remain research-only."
        )