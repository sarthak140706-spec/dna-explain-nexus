from typing import (
    List,
    Optional,
    Union,
)

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


# ============================================================
# Supported symbols
# ============================================================

CANONICAL_BASES = {
    "A",
    "C",
    "G",
    "T",
}

CANONICAL_AMINO_ACIDS = {
    "A",
    "R",
    "N",
    "D",
    "C",
    "Q",
    "E",
    "G",
    "H",
    "I",
    "L",
    "K",
    "M",
    "F",
    "P",
    "S",
    "T",
    "W",
    "Y",
    "V",
}


# ============================================================
# Request
# ============================================================

class VariantRequest(BaseModel):

    gene_symbol: str = Field(
        min_length=1,
        max_length=50,
        examples=["TP53"],
    )

    chromosome: Optional[str] = Field(
        default=None,
        examples=["17"],
    )

    position: Optional[int] = Field(
        default=None,
        gt=0,
        examples=[7674208],
    )

    reference_allele: str = Field(
        min_length=1,
        max_length=1,
        examples=["A"],
    )

    alternate_allele: str = Field(
        min_length=1,
        max_length=1,
        examples=["G"],
    )

    protein_position: int = Field(
        gt=0,
        examples=[252],
    )

    reference_amino_acid: str = Field(
        min_length=1,
        max_length=1,
        examples=["L"],
    )

    alternate_amino_acid: str = Field(
        min_length=1,
        max_length=1,
        examples=["P"],
    )

    dna_change: Optional[str] = Field(
        default=None,
        examples=["c.755T>C"],
    )

    protein_change: Optional[str] = Field(
        default=None,
        examples=["p.Leu252Pro"],
    )

    # --------------------------------------------------------
    # Normalization
    # --------------------------------------------------------

    @field_validator(
        "gene_symbol"
    )
    @classmethod
    def normalize_gene_symbol(
        cls,
        value: str,
    ) -> str:

        normalized = (
            value.strip().upper()
        )

        if not normalized:

            raise ValueError(
                "gene_symbol cannot be empty."
            )

        return normalized

    @field_validator(
        "chromosome"
    )
    @classmethod
    def normalize_chromosome(
        cls,
        value: Optional[str],
    ) -> Optional[str]:

        if value is None:
            return None

        normalized = (
            str(value)
            .strip()
            .upper()
        )

        if normalized.startswith(
            "CHR"
        ):
            normalized = (
                normalized[3:]
            )

        canonical = {
            *[
                str(number)
                for number
                in range(1, 23)
            ],
            "X",
            "Y",
        }

        if normalized not in canonical:

            raise ValueError(
                "Chromosome must be one "
                "of 1-22, X, or Y."
            )

        return normalized

    @field_validator(
        "reference_allele",
        "alternate_allele",
    )
    @classmethod
    def validate_base(
        cls,
        value: str,
    ) -> str:

        normalized = (
            value.strip().upper()
        )

        if normalized not in (
            CANONICAL_BASES
        ):

            raise ValueError(
                "Allele must be one of "
                "A, C, G, T."
            )

        return normalized

    @field_validator(
        "reference_amino_acid",
        "alternate_amino_acid",
    )
    @classmethod
    def validate_amino_acid(
        cls,
        value: str,
    ) -> str:

        normalized = (
            value.strip().upper()
        )

        if normalized not in (
            CANONICAL_AMINO_ACIDS
        ):

            raise ValueError(
                "Amino acid must be one "
                "of the 20 canonical "
                "one-letter amino-acid codes."
            )

        return normalized

    # --------------------------------------------------------
    # Cross-field rules
    # --------------------------------------------------------

    @model_validator(
        mode="after"
    )
    def validate_variant_relationships(
        self,
    ):

        if (
            self.reference_allele
            == self.alternate_allele
        ):

            raise ValueError(
                "Reference and alternate "
                "alleles must differ."
            )

        if (
            self.reference_amino_acid
            == self.alternate_amino_acid
        ):

            raise ValueError(
                "Reference and alternate "
                "amino acids must differ."
            )

        if (
            self.chromosome is None
        ) != (
            self.position is None
        ):

            raise ValueError(
                "chromosome and position "
                "must either both be provided "
                "or both be omitted."
            )

        return self


# ============================================================
# Variant identity
# ============================================================

class VariantIdentity(BaseModel):

    gene_symbol: str

    chromosome: Optional[str] = None

    position: Optional[int] = None

    reference_allele: str

    alternate_allele: str

    protein_position: int

    reference_amino_acid: str

    alternate_amino_acid: str

    dna_change: Optional[str] = None

    protein_change: Optional[str] = None


# ============================================================
# Protein validation
# ============================================================

class ProteinValidationResult(
    BaseModel
):

    performed: bool = True

    valid: bool

    accession: Optional[str] = None

    protein_name: Optional[str] = None

    reviewed: Optional[bool] = None

    protein_length: Optional[
        int
    ] = None

    sequence_reference_amino_acid: Optional[
        str
    ] = None

    position_matches_reference: Optional[
        bool
    ] = None

    amino_acid_change: Optional[
        str
    ] = None

    source: Optional[str] = None

    validation_status: str

    error: Optional[str] = None


# ============================================================
# Genomic / VEP validation
# ============================================================

class GenomicValidationResult(
    BaseModel
):

    performed: bool

    valid: Optional[bool] = None

    annotation_status: Optional[
        str
    ] = None

    most_severe_consequence: Optional[
        str
    ] = None

    transcript_id: Optional[
        str
    ] = None

    consequence_terms: Optional[
        Union[
            str,
            List[str],
        ]
    ] = None

    is_missense: Optional[
        bool
    ] = None

    mane_select: Optional[
        str
    ] = None

    canonical: Optional[
        Union[
            str,
            int,
            bool,
        ]
    ] = None

    vep_dna_change: Optional[
        str
    ] = None

    vep_protein_change: Optional[
        str
    ] = None

    dna_match: Optional[
        bool
    ] = None

    protein_match: Optional[
        bool
    ] = None

    verification_status: Optional[
        str
    ] = None

    selection_reason: Optional[
        str
    ] = None

    error: Optional[str] = None


# ============================================================
# Final validation response
# ============================================================

class VariantValidationResponse(
    BaseModel
):

    success: bool = True

    variant: VariantIdentity

    valid: bool

    validation_status: str

    protein_validation: (
        ProteinValidationResult
    )

    genomic_validation: (
        GenomicValidationResult
    )

    research_only: bool = True

    disclaimer: str