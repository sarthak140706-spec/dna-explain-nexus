from typing import (
    List,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

from backend.api.schemas.variant import (
    VariantIdentity,
)


# ============================================================
# Protein identity
# ============================================================

class ProteinIdentityResponse(
    BaseModel
):

    accession: str

    gene_symbol: str

    protein_name: str

    organism: str

    sequence_length: int = Field(
        gt=0,
    )

    reviewed: bool

    entry_name: Optional[
        str
    ] = None

    source: str = "UniProtKB"


# ============================================================
# Protein feature
# ============================================================

class ProteinFeatureResponse(
    BaseModel
):

    feature_type: str

    start: int = Field(
        gt=0,
    )

    end: int = Field(
        gt=0,
    )

    description: Optional[
        str
    ] = None

    feature_id: Optional[
        str
    ] = None

    evidence: List[str] = Field(
        default_factory=list,
    )

    distance_to_variant: Optional[
        int
    ] = Field(
        default=None,
        ge=0,
    )

    overlaps_variant: bool = False


# ============================================================
# Sequence context
# ============================================================

class ProteinSequenceContextResponse(
    BaseModel
):

    protein_position: int = Field(
        gt=0,
    )

    reference_amino_acid: str

    sequence_reference_amino_acid: str

    position_matches_reference: bool

    window_start: int = Field(
        gt=0,
    )

    window_end: int = Field(
        gt=0,
    )

    sequence_window: str

    variant_index_in_window: int = Field(
        ge=0,
    )

    protein_length: int = Field(
        gt=0,
    )


# ============================================================
# Protein-relative variant information
# ============================================================

class ProteinVariantResponse(
    BaseModel
):

    gene_symbol: str

    protein_position: int = Field(
        gt=0,
    )

    reference_amino_acid: str

    alternate_amino_acid: str

    amino_acid_change: str

    normalized_position: float = Field(
        gt=0.0,
        le=1.0,
    )


# ============================================================
# Variant visualization marker
# ============================================================

class VariantMarkerResponse(
    BaseModel
):

    position: int = Field(
        gt=0,
    )

    reference_amino_acid: str

    alternate_amino_acid: str

    label: str


# ============================================================
# Visualization feature
# ============================================================

class VisualizationFeatureResponse(
    BaseModel
):

    feature_type: str

    start: int = Field(
        gt=0,
    )

    end: int = Field(
        gt=0,
    )

    start_fraction: float = Field(
        gt=0.0,
        le=1.0,
    )

    end_fraction: float = Field(
        gt=0.0,
        le=1.0,
    )

    description: Optional[
        str
    ] = None

    feature_id: Optional[
        str
    ] = None

    evidence: List[str] = Field(
        default_factory=list,
    )

    overlaps_variant: bool = False

    distance_to_variant: Optional[
        int
    ] = Field(
        default=None,
        ge=0,
    )


# ============================================================
# Visualization track
# ============================================================

class VisualizationTrackResponse(
    BaseModel
):

    track_type: str

    label: str

    features: List[
        VisualizationFeatureResponse
    ] = Field(
        default_factory=list,
    )


# ============================================================
# Complete protein context response
# ============================================================

class ProteinContextResponse(
    BaseModel
):

    success: bool = True

    # Original API input identity.
    variant: VariantIdentity

    # Protein-relative information generated
    # by the frozen Sprint 6 engine.
    protein_variant: (
        ProteinVariantResponse
    )

    protein: (
        ProteinIdentityResponse
    )

    sequence_context: (
        ProteinSequenceContextResponse
    )

    overlapping_features: List[
        ProteinFeatureResponse
    ] = Field(
        default_factory=list,
    )

    nearby_features: List[
        ProteinFeatureResponse
    ] = Field(
        default_factory=list,
    )

    visualization_tracks: List[
        VisualizationTrackResponse
    ] = Field(
        default_factory=list,
    )

    variant_marker: Optional[
        VariantMarkerResponse
    ] = None

    protein_context_version: str

    visualization_version: str

    interpretation: str

    research_only: bool = True

    disclaimer: str