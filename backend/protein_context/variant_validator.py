import sys
from pathlib import Path
from typing import Any, Dict


# ============================================================
# Make project root importable
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

from backend.protein_context.config import (
    SUPPORTED_AMINO_ACIDS,
)

from backend.protein_context.parser import (
    parse_uniprot_entry,
    verify_parsed_protein,
)

from backend.protein_context.uniprot_client import (
    get_reviewed_human_protein,
)


# ============================================================
# Exceptions
# ============================================================

class ProteinVariantValidationError(
    ValueError
):
    pass


class ProteinPositionOutOfRangeError(
    ProteinVariantValidationError
):
    pass


class ReferenceAminoAcidMismatchError(
    ProteinVariantValidationError
):
    pass


# ============================================================
# Input normalization
# ============================================================

def normalize_amino_acid(
    amino_acid: str,
    field_name: str,
) -> str:

    if amino_acid is None:

        raise ProteinVariantValidationError(
            f"{field_name} is required."
        )

    amino_acid = (
        str(amino_acid)
        .strip()
        .upper()
    )

    if amino_acid not in (
        SUPPORTED_AMINO_ACIDS
    ):

        raise ProteinVariantValidationError(
            f"{field_name} must be one "
            "canonical amino-acid code."
        )

    return amino_acid


def normalize_protein_position(
    protein_position: Any,
) -> int:

    try:

        position = int(
            protein_position
        )

    except (
        TypeError,
        ValueError,
    ) as error:

        raise ProteinVariantValidationError(
            "Protein position must be "
            "an integer."
        ) from error

    if position <= 0:

        raise ProteinVariantValidationError(
            "Protein position must "
            "be positive."
        )

    return position


# ============================================================
# Core sequence validation
# ============================================================

def validate_variant_against_sequence(
    sequence: str,
    protein_position: Any,
    reference_aa: str,
    alternate_aa: str,
) -> Dict[str, Any]:

    if not sequence:

        raise ProteinVariantValidationError(
            "Protein sequence is required."
        )

    sequence = (
        str(sequence)
        .strip()
        .upper()
    )

    position = (
        normalize_protein_position(
            protein_position
        )
    )

    reference_aa = (
        normalize_amino_acid(
            reference_aa,
            "Reference amino acid",
        )
    )

    alternate_aa = (
        normalize_amino_acid(
            alternate_aa,
            "Alternate amino acid",
        )
    )

    if reference_aa == alternate_aa:

        raise ProteinVariantValidationError(
            "Reference and alternate "
            "amino acids must differ."
        )

    protein_length = len(
        sequence
    )

    if position > protein_length:

        raise ProteinPositionOutOfRangeError(
            f"Protein position {position} "
            f"exceeds protein length "
            f"{protein_length}."
        )

    # Biological positions are 1-based.
    # Python sequence indices are 0-based.
    sequence_reference_aa = (
        sequence[
            position - 1
        ]
    )

    position_matches_reference = (
        sequence_reference_aa
        == reference_aa
    )

    if not position_matches_reference:

        raise ReferenceAminoAcidMismatchError(
            "Reference amino-acid mismatch: "
            f"input expects {reference_aa}"
            f"{position}, but UniProt "
            f"contains {sequence_reference_aa}"
            f"{position}."
        )

    return {
        "protein_position": (
            position
        ),

        "reference_amino_acid": (
            reference_aa
        ),

        "alternate_amino_acid": (
            alternate_aa
        ),

        "sequence_reference_amino_acid": (
            sequence_reference_aa
        ),

        "position_matches_reference": (
            True
        ),

        "protein_length": (
            protein_length
        ),

        "amino_acid_change": (
            f"{reference_aa}"
            f"{position}"
            f"{alternate_aa}"
        ),
    }


# ============================================================
# Gene-level validation
# ============================================================

def validate_variant_for_gene(
    gene_symbol: str,
    protein_position: Any,
    reference_aa: str,
    alternate_aa: str,
) -> Dict[str, Any]:

    result = (
        get_reviewed_human_protein(
            gene_symbol
        )
    )

    parsed = (
        parse_uniprot_entry(
            result[
                "entry"
            ]
        )
    )

    verify_parsed_protein(
        parsed
    )

    identity = parsed[
        "identity"
    ]

    sequence = parsed[
        "sequence"
    ]

    requested_gene = (
        str(
            gene_symbol
        )
        .strip()
        .upper()
    )

    if (
        identity.gene_symbol
        != requested_gene
    ):

        raise ProteinVariantValidationError(
            "Retrieved UniProt gene "
            "does not match requested gene."
        )

    validation = (
        validate_variant_against_sequence(
            sequence=sequence,
            protein_position=protein_position,
            reference_aa=reference_aa,
            alternate_aa=alternate_aa,
        )
    )

    return {
        "gene_symbol": (
            identity.gene_symbol
        ),

        "accession": (
            identity.accession
        ),

        "protein_name": (
            identity.protein_name
        ),

        "reviewed": (
            identity.reviewed
        ),

        **validation,

        "source": (
            "UniProtKB"
        ),

        "reference_validation": (
            "matched"
        ),
    }


# ============================================================
# CLI smoke test
# ============================================================

def main():

    print(
        "GeneMirror Sprint 6 "
        "Variant-to-Protein Position Validation"
    )

    print(
        "=" * 72
    )

    gene = "TP53"
    position = 248
    reference = "R"
    alternate = "H"

    print(
        f"\nValidating variant: "
        f"{gene} "
        f"{reference}{position}{alternate}"
    )

    result = (
        validate_variant_for_gene(
            gene_symbol=gene,
            protein_position=position,
            reference_aa=reference,
            alternate_aa=alternate,
        )
    )

    print(
        f"Accession: "
        f"{result['accession']}"
    )

    print(
        f"Protein: "
        f"{result['protein_name']}"
    )

    print(
        f"Protein length: "
        f"{result['protein_length']}"
    )

    print(
        f"Sequence residue at "
        f"{position}: "
        f"{result['sequence_reference_amino_acid']}"
    )

    print(
        "Reference match:",
        result[
            "position_matches_reference"
        ],
    )

    print(
        "Validated change:",
        result[
            "amino_acid_change"
        ],
    )

    print(
        "\n✅ Variant-to-protein "
        "validation completed."
    )


if __name__ == "__main__":
    main()