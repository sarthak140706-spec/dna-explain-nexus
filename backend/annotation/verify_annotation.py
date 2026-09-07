from pathlib import Path

import pandas as pd

from config import (
    ANNOTATED_DATASET_PATH,
)


EXPECTED_GENES = {
    "TP53",
    "BRCA1",
    "CFTR",
    "HBB",
    "APOE",
    "MTHFR",
}

EXPECTED_VARIANTS_PER_GENE = 20
EXPECTED_TOTAL_ROWS = 120

VALID_BASES = {
    "A",
    "C",
    "G",
    "T",
}

VALID_CHROMOSOMES = {
    *(str(i) for i in range(1, 23)),
    "X",
    "Y",
}


def print_check(
    label: str,
    value: int,
) -> bool:
    """
    Print one verification check.

    Returns True when the error count
    is zero.
    """

    passed = value == 0

    symbol = (
        "✅"
        if passed
        else "❌"
    )

    print(
        f"{symbol} {label}: {value}"
    )

    return passed


def verify_annotated_dataset(
    dataset_path: Path,
) -> bool:
    """
    Verify the GeneMirror Sprint 3
    annotated dataset.
    """

    print(
        "GeneMirror Annotation Dataset Verification"
    )

    print(
        "=" * 65
    )

    print(
        f"\nDataset:\n{dataset_path}"
    )

    if not dataset_path.exists():

        print(
            "\n❌ Annotated dataset "
            "does not exist."
        )

        return False

    file_size_mb = (
        dataset_path.stat().st_size
        / (1024 * 1024)
    )

    print(
        f"\nFile size: "
        f"{file_size_mb:.2f} MB"
    )

    dataframe = pd.read_csv(
        dataset_path,
        low_memory=False,
    )

    print(
        f"\nTotal rows: "
        f"{len(dataframe)}"
    )

    print(
        f"Total columns: "
        f"{len(dataframe.columns)}"
    )

    # ==================================================
    # Required columns
    # ==================================================

    required_columns = {
        "variant_key",
        "variation_id",
        "gene_symbol",
        "chromosome",
        "position",
        "reference_allele",
        "alternate_allele",
        "annotation_status",
        "most_severe_consequence",
        "transcript_id",
        "biotype",
        "consequence_terms",
        "is_missense",
        "mane_select",
        "canonical",
        "protein_start",
        "source_dna_change",
        "source_protein_change",
        "vep_dna_change",
        "vep_protein_change",
        "dna_match",
        "protein_match",
        "verification_status",
        "selection_reason",
    }

    missing_columns = (
        required_columns
        - set(
            dataframe.columns
        )
    )

    print(
        "\nRequired columns"
    )

    print(
        "-" * 65
    )

    if missing_columns:

        print(
            "❌ Missing columns:"
        )

        for column in sorted(
            missing_columns
        ):

            print(
                f"   - {column}"
            )

        return False

    print(
        "✅ Required columns verified."
    )

    # ==================================================
    # Integrity checks
    # ==================================================

    failures = []

    print(
        "\nCritical integrity checks"
    )

    print(
        "-" * 65
    )

    wrong_row_count = int(
        len(dataframe)
        != EXPECTED_TOTAL_ROWS
    )

    if not print_check(
        "Unexpected total row count",
        wrong_row_count,
    ):
        failures.append(
            "row_count"
        )

    missing_variant_keys = (
        dataframe[
            "variant_key"
        ].isna().sum()
    )

    if not print_check(
        "Missing variant keys",
        int(
            missing_variant_keys
        ),
    ):
        failures.append(
            "missing_variant_keys"
        )

    duplicate_variant_keys = (
        dataframe[
            "variant_key"
        ].duplicated().sum()
    )

    if not print_check(
        "Duplicate variant keys",
        int(
            duplicate_variant_keys
        ),
    ):
        failures.append(
            "duplicate_variant_keys"
        )

    missing_genes = (
        dataframe[
            "gene_symbol"
        ].isna().sum()
    )

    if not print_check(
        "Missing gene symbols",
        int(
            missing_genes
        ),
    ):
        failures.append(
            "missing_gene_symbols"
        )

    invalid_genes = (
        ~dataframe[
            "gene_symbol"
        ].isin(
            EXPECTED_GENES
        )
    ).sum()

    if not print_check(
        "Unexpected genes",
        int(
            invalid_genes
        ),
    ):
        failures.append(
            "unexpected_genes"
        )

    missing_positions = (
        dataframe[
            "position"
        ].isna().sum()
    )

    if not print_check(
        "Missing genomic positions",
        int(
            missing_positions
        ),
    ):
        failures.append(
            "missing_positions"
        )

    invalid_positions = (
        pd.to_numeric(
            dataframe[
                "position"
            ],
            errors="coerce",
        )
        <= 0
    ).sum()

    if not print_check(
        "Invalid genomic positions",
        int(
            invalid_positions
        ),
    ):
        failures.append(
            "invalid_positions"
        )

    chromosomes = (
        dataframe[
            "chromosome"
        ]
        .astype(str)
        .str.replace(
            ".0",
            "",
            regex=False,
        )
        .str.replace(
            "chr",
            "",
            regex=False,
        )
    )

    invalid_chromosomes = (
        ~chromosomes.isin(
            VALID_CHROMOSOMES
        )
    ).sum()

    if not print_check(
        "Invalid chromosomes",
        int(
            invalid_chromosomes
        ),
    ):
        failures.append(
            "invalid_chromosomes"
        )

    references = (
        dataframe[
            "reference_allele"
        ]
        .astype(str)
        .str.upper()
    )

    alternates = (
        dataframe[
            "alternate_allele"
        ]
        .astype(str)
        .str.upper()
    )

    invalid_reference = (
        ~references.isin(
            VALID_BASES
        )
    ).sum()

    if not print_check(
        "Invalid reference alleles",
        int(
            invalid_reference
        ),
    ):
        failures.append(
            "invalid_reference"
        )

    invalid_alternate = (
        ~alternates.isin(
            VALID_BASES
        )
    ).sum()

    if not print_check(
        "Invalid alternate alleles",
        int(
            invalid_alternate
        ),
    ):
        failures.append(
            "invalid_alternate"
        )

    same_alleles = (
        references
        == alternates
    ).sum()

    if not print_check(
        "REF equals ALT",
        int(
            same_alleles
        ),
    ):
        failures.append(
            "same_alleles"
        )

    # ==================================================
    # Annotation checks
    # ==================================================

    print(
        "\nAnnotation checks"
    )

    print(
        "-" * 65
    )

    annotation_errors = (
        dataframe[
            "annotation_status"
        ]
        .fillna("")
        .ne(
            "annotated"
        )
        .sum()
    )

    if not print_check(
        "Non-annotated rows",
        int(
            annotation_errors
        ),
    ):
        failures.append(
            "annotation_errors"
        )

    missing_transcripts = (
        dataframe[
            "transcript_id"
        ].isna().sum()
    )

    if not print_check(
        "Missing transcript IDs",
        int(
            missing_transcripts
        ),
    ):
        failures.append(
            "missing_transcripts"
        )

    invalid_biotype = (
        dataframe[
            "biotype"
        ]
        .fillna("")
        .ne(
            "protein_coding"
        )
        .sum()
    )

    if not print_check(
        "Non-protein-coding selected transcripts",
        int(
            invalid_biotype
        ),
    ):
        failures.append(
            "invalid_biotype"
        )

    non_missense = (
        ~dataframe[
            "consequence_terms"
        ]
        .fillna("")
        .str.contains(
            "missense_variant",
            regex=False,
        )
    ).sum()

    if not print_check(
        "Selected transcripts without missense_variant",
        int(
            non_missense
        ),
    ):
        failures.append(
            "non_missense"
        )

    invalid_missense_flag = (
        ~dataframe[
            "is_missense"
        ]
        .astype(str)
        .str.lower()
        .isin(
            {
                "true",
                "1",
            }
        )
    ).sum()

    if not print_check(
        "Invalid is_missense flags",
        int(
            invalid_missense_flag
        ),
    ):
        failures.append(
            "invalid_missense_flag"
        )

    missing_protein_positions = (
        dataframe[
            "protein_start"
        ].isna().sum()
    )

    if not print_check(
        "Missing protein positions",
        int(
            missing_protein_positions
        ),
    ):
        failures.append(
            "missing_protein_positions"
        )

    invalid_protein_positions = (
        pd.to_numeric(
            dataframe[
                "protein_start"
            ],
            errors="coerce",
        )
        <= 0
    ).sum()

    if not print_check(
        "Invalid protein positions",
        int(
            invalid_protein_positions
        ),
    ):
        failures.append(
            "invalid_protein_positions"
        )

    # ==================================================
    # HGVS agreement
    # ==================================================

    print(
        "\nHGVS agreement checks"
    )

    print(
        "-" * 65
    )

    missing_source_dna = (
        dataframe[
            "source_dna_change"
        ].isna().sum()
    )

    if not print_check(
        "Missing source DNA changes",
        int(
            missing_source_dna
        ),
    ):
        failures.append(
            "missing_source_dna"
        )

    missing_source_protein = (
        dataframe[
            "source_protein_change"
        ].isna().sum()
    )

    if not print_check(
        "Missing source protein changes",
        int(
            missing_source_protein
        ),
    ):
        failures.append(
            "missing_source_protein"
        )

    missing_vep_dna = (
        dataframe[
            "vep_dna_change"
        ].isna().sum()
    )

    if not print_check(
        "Missing VEP DNA changes",
        int(
            missing_vep_dna
        ),
    ):
        failures.append(
            "missing_vep_dna"
        )

    missing_vep_protein = (
        dataframe[
            "vep_protein_change"
        ].isna().sum()
    )

    if not print_check(
        "Missing VEP protein changes",
        int(
            missing_vep_protein
        ),
    ):
        failures.append(
            "missing_vep_protein"
        )

    dna_mismatches = (
        ~dataframe[
            "dna_match"
        ]
        .astype(str)
        .str.lower()
        .isin(
            {
                "true",
                "1",
            }
        )
    ).sum()

    if not print_check(
        "DNA mismatches",
        int(
            dna_mismatches
        ),
    ):
        failures.append(
            "dna_mismatches"
        )

    protein_mismatches = (
        ~dataframe[
            "protein_match"
        ]
        .astype(str)
        .str.lower()
        .isin(
            {
                "true",
                "1",
            }
        )
    ).sum()

    if not print_check(
        "Protein mismatches",
        int(
            protein_mismatches
        ),
    ):
        failures.append(
            "protein_mismatches"
        )

    non_full_match = (
        dataframe[
            "verification_status"
        ]
        .fillna("")
        .ne(
            "full_match"
        )
        .sum()
    )

    if not print_check(
        "Rows without full_match",
        int(
            non_full_match
        ),
    ):
        failures.append(
            "non_full_match"
        )

    # ==================================================
    # Transcript-selection checks
    # ==================================================

    print(
        "\nTranscript selection checks"
    )

    print(
        "-" * 65
    )

    missing_selection_reason = (
        dataframe[
            "selection_reason"
        ].isna().sum()
    )

    if not print_check(
        "Missing selection reasons",
        int(
            missing_selection_reason
        ),
    ):
        failures.append(
            "missing_selection_reason"
        )

    no_selection_priority = (
        ~dataframe[
            "selection_reason"
        ]
        .fillna("")
        .str.contains(
            "mane_select|mane_plus_clinical|canonical|protein_coding",
            regex=True,
        )
    ).sum()

    if not print_check(
        "Rows without documented transcript priority",
        int(
            no_selection_priority
        ),
    ):
        failures.append(
            "selection_priority"
        )

    # ==================================================
    # Gene coverage
    # ==================================================

    print(
        "\nDemo gene coverage"
    )

    print(
        "-" * 65
    )

    gene_counts = (
        dataframe[
            "gene_symbol"
        ].value_counts()
    )

    for gene in sorted(
        EXPECTED_GENES
    ):

        count = int(
            gene_counts.get(
                gene,
                0,
            )
        )

        symbol = (
            "✅"
            if count
            == EXPECTED_VARIANTS_PER_GENE
            else "❌"
        )

        print(
            f"{symbol} "
            f"{gene}: "
            f"{count} variants"
        )

        if (
            count
            != EXPECTED_VARIANTS_PER_GENE
        ):
            failures.append(
                f"gene_count_{gene}"
            )

    # ==================================================
    # Summary
    # ==================================================

    print(
        "\nVerification summary"
    )

    print(
        "=" * 65
    )

    print(
        f"Rows checked: "
        f"{len(dataframe)}"
    )

    print(
        f"Unique variants: "
        f"{dataframe['variant_key'].nunique()}"
    )

    print(
        f"Unique genes: "
        f"{dataframe['gene_symbol'].nunique()}"
    )

    print(
        "\nVerification status distribution:"
    )

    print(
        dataframe[
            "verification_status"
        ].value_counts(
            dropna=False
        )
    )

    print(
        "\nTranscript selection reasons:"
    )

    print(
        dataframe[
            "selection_reason"
        ].value_counts(
            dropna=False
        ).head(
            10
        )
    )

    print(
        "\n"
        + "=" * 65
    )

    if failures:

        print(
            "❌ SPRINT 3 ANNOTATION "
            "VERIFICATION FAILED"
        )

        print(
            "\nFailed checks:"
        )

        for failure in failures:

            print(
                f" - {failure}"
            )

        return False

    print(
        "✅ SPRINT 3 ANNOTATION "
        "VERIFICATION PASSED"
    )

    return True


if __name__ == "__main__":

    success = (
        verify_annotated_dataset(
            ANNOTATED_DATASET_PATH
        )
    )

    if not success:

        raise SystemExit(
            1
        )