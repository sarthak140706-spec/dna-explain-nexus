import sys
from pathlib import Path
from typing import Any, Dict


# ============================================================
# Make project root importable
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Imports
# ============================================================

from backend.protein_context.config import (
    DEFAULT_SEQUENCE_WINDOW_RADIUS,
)

from backend.protein_context.contracts import (
    SequenceContext,
)

from backend.protein_context.parser import (
    parse_uniprot_entry,
    verify_parsed_protein,
)

from backend.protein_context.uniprot_client import (
    get_reviewed_human_protein,
)

from backend.protein_context.variant_validator import (
    validate_variant_against_sequence,
)


# ============================================================
# Sequence window helper
# ============================================================

def build_sequence_context(
    sequence: str,
    protein_position: int,
    reference_aa: str,
    alternate_aa: str,
    window_radius: int = (
        DEFAULT_SEQUENCE_WINDOW_RADIUS
    ),
) -> SequenceContext:

    if window_radius < 0:

        raise ValueError(
            "Sequence window radius "
            "cannot be negative."
        )

    validation = (
        validate_variant_against_sequence(
            sequence=sequence,
            protein_position=protein_position,
            reference_aa=reference_aa,
            alternate_aa=alternate_aa,
        )
    )

    position = validation[
        "protein_position"
    ]

    protein_length = validation[
        "protein_length"
    ]

    window_start = max(
        1,
        position - window_radius,
    )

    window_end = min(
        protein_length,
        position + window_radius,
    )

    # Convert 1-based biological coordinates
    # to Python slicing coordinates.
    sequence_window = sequence[
        window_start - 1
        :
        window_end
    ]

    variant_index_in_window = (
        position
        - window_start
    )

    if not (
        0
        <= variant_index_in_window
        < len(sequence_window)
    ):

        raise ValueError(
            "Variant index is outside "
            "the generated sequence window."
        )

    window_reference = sequence_window[
        variant_index_in_window
    ]

    if (
        window_reference
        != validation[
            "sequence_reference_amino_acid"
        ]
    ):

        raise ValueError(
            "Sequence-window reference "
            "residue does not match "
            "validated residue."
        )

    return SequenceContext(
        protein_position=position,
        reference_amino_acid=validation[
            "reference_amino_acid"
        ],
        sequence_reference_amino_acid=(
            validation[
                "sequence_reference_amino_acid"
            ]
        ),
        position_matches_reference=True,
        window_start=window_start,
        window_end=window_end,
        sequence_window=sequence_window,
        variant_index_in_window=(
            variant_index_in_window
        ),
        protein_length=protein_length,
    )


# ============================================================
# Gene-level context engine
# ============================================================

def get_local_protein_context(
    gene_symbol: str,
    protein_position: int,
    reference_aa: str,
    alternate_aa: str,
    window_radius: int = (
        DEFAULT_SEQUENCE_WINDOW_RADIUS
    ),
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

    context = (
        build_sequence_context(
            sequence=sequence,
            protein_position=protein_position,
            reference_aa=reference_aa,
            alternate_aa=alternate_aa,
            window_radius=window_radius,
        )
    )

    return {
        "protein": identity,
        "sequence_context": context,
        "amino_acid_change": (
            f"{context.reference_amino_acid}"
            f"{context.protein_position}"
            f"{alternate_aa.upper()}"
        ),
        "source": "UniProtKB",
    }


# ============================================================
# Verification helper
# ============================================================

def verify_local_context(
    result: Dict[str, Any],
) -> None:

    protein = result[
        "protein"
    ]

    context = result[
        "sequence_context"
    ]

    if (
        context.protein_length
        != protein.sequence_length
    ):

        raise ValueError(
            "Protein length mismatch "
            "between identity and context."
        )

    if (
        context.window_start
        < 1
    ):

        raise ValueError(
            "Sequence context starts "
            "before protein boundary."
        )

    if (
        context.window_end
        > protein.sequence_length
    ):

        raise ValueError(
            "Sequence context exceeds "
            "protein boundary."
        )

    expected_window_length = (
        context.window_end
        - context.window_start
        + 1
    )

    if (
        len(
            context.sequence_window
        )
        != expected_window_length
    ):

        raise ValueError(
            "Sequence window length "
            "does not match coordinates."
        )

    residue = (
        context.sequence_window[
            context.variant_index_in_window
        ]
    )

    if (
        residue
        != context.reference_amino_acid
    ):

        raise ValueError(
            "Variant residue inside "
            "sequence window is incorrect."
        )


# ============================================================
# CLI smoke test
# ============================================================

def main():

    print(
        "GeneMirror Sprint 6 "
        "Local Protein Context Engine"
    )

    print(
        "=" * 72
    )

    gene = "TP53"
    position = 248
    reference = "R"
    alternate = "H"

    result = (
        get_local_protein_context(
            gene_symbol=gene,
            protein_position=position,
            reference_aa=reference,
            alternate_aa=alternate,
        )
    )

    verify_local_context(
        result
    )

    protein = result[
        "protein"
    ]

    context = result[
        "sequence_context"
    ]

    print(
        f"\nGene: "
        f"{protein.gene_symbol}"
    )

    print(
        f"Accession: "
        f"{protein.accession}"
    )

    print(
        f"Protein length: "
        f"{protein.sequence_length}"
    )

    print(
        f"Variant: "
        f"{result['amino_acid_change']}"
    )

    print(
        f"Window: "
        f"{context.window_start}-"
        f"{context.window_end}"
    )

    print(
        f"Window length: "
        f"{len(context.sequence_window)}"
    )

    print(
        f"Variant index in window: "
        f"{context.variant_index_in_window}"
    )

    print(
        f"Sequence window: "
        f"{context.sequence_window}"
    )

    print(
        "Reference residue in window:",
        context.sequence_window[
            context.variant_index_in_window
        ],
    )

    print(
        "\n✅ Local protein context "
        "engine completed."
    )


if __name__ == "__main__":
    main()