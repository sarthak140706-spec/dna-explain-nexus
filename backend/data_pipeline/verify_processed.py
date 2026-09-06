from pathlib import Path

import pandas as pd

from config import PROCESSED_DATASET_PATH


CHUNK_SIZE = 100_000


REQUIRED_COLUMNS = {
    "allele_id",
    "variation_id",
    "gene_id",
    "gene_symbol",
    "clinvar_name",
    "source_clinical_significance",
    "assembly",
    "chromosome",
    "position",
    "reference_allele",
    "alternate_allele",
    "review_status",
    "dna_change",
    "protein_change",
    "is_missense",
    "reference_aa",
    "protein_position",
    "alternate_aa",
    "amino_acid_change",
    "variant_key",
}


VALID_AMINO_ACIDS = {
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


VALID_CHROMOSOMES = {
    *(str(i) for i in range(1, 23)),
    "X",
    "Y",
}


DEMO_GENES = {
    "TP53",
    "BRCA1",
    "CFTR",
    "HBB",
    "APOE",
    "MTHFR",
}


def verify_columns() -> list[str]:
    """
    Verify that all required GeneMirror columns
    are present in the processed dataset.
    """

    header = pd.read_csv(
        PROCESSED_DATASET_PATH,
        nrows=0,
    )

    columns = set(header.columns)

    missing = sorted(
        REQUIRED_COLUMNS - columns
    )

    return missing


def verify_processed_dataset():
    """
    Run integrity checks on the complete
    GeneMirror processed dataset.
    """

    print(
        "GeneMirror Processed Dataset Verification"
    )

    print("=" * 55)

    if not PROCESSED_DATASET_PATH.exists():

        raise FileNotFoundError(
            f"Processed dataset not found: "
            f"{PROCESSED_DATASET_PATH}"
        )

    file_size_mb = (
        PROCESSED_DATASET_PATH.stat().st_size
        / (1024 ** 2)
    )

    print(
        f"\nDataset:"
        f"\n{PROCESSED_DATASET_PATH}"
    )

    print(
        f"\nFile size: "
        f"{file_size_mb:.2f} MB"
    )

    # --------------------------------------------------
    # Column verification
    # --------------------------------------------------

    missing_columns = verify_columns()

    if missing_columns:

        print(
            "\n❌ Missing required columns:"
        )

        for column in missing_columns:
            print(
                f"- {column}"
            )

        raise ValueError(
            "Processed dataset schema verification failed."
        )

    print(
        "\n✅ Required columns verified."
    )

    # --------------------------------------------------
    # Global counters
    # --------------------------------------------------

    total_rows = 0

    missing_gene_symbol = 0
    missing_variant_key = 0
    missing_protein_change = 0
    missing_protein_position = 0
    missing_reference_aa = 0
    missing_alternate_aa = 0

    invalid_assembly = 0
    invalid_reference = 0
    invalid_alternate = 0
    reference_equals_alternate = 0

    invalid_reference_aa = 0
    invalid_alternate_aa = 0

    invalid_protein_position = 0
    non_missense_rows = 0
    invalid_chromosome = 0

    duplicate_variant_keys = 0

    seen_variant_keys = set()
    genes = set()

    demo_gene_counts = {
        gene: 0
        for gene in DEMO_GENES
    }

    clinical_significance_counts = {}

    # --------------------------------------------------
    # Chunked verification
    # --------------------------------------------------

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            PROCESSED_DATASET_PATH,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        ),
        start=1,
    ):

        rows = len(chunk)

        total_rows += rows

        print(
            f"\rVerifying chunk {chunk_number} "
            f"| Rows checked: {total_rows:,}",
            end="",
        )

        # ----------------------------------------------
        # Missing critical values
        # ----------------------------------------------

        missing_gene_symbol += int(
            chunk[
                "gene_symbol"
            ].isna().sum()
        )

        missing_variant_key += int(
            chunk[
                "variant_key"
            ].isna().sum()
        )

        missing_protein_change += int(
            chunk[
                "protein_change"
            ].isna().sum()
        )

        missing_protein_position += int(
            chunk[
                "protein_position"
            ].isna().sum()
        )

        missing_reference_aa += int(
            chunk[
                "reference_aa"
            ].isna().sum()
        )

        missing_alternate_aa += int(
            chunk[
                "alternate_aa"
            ].isna().sum()
        )

        # ----------------------------------------------
        # Assembly
        # ----------------------------------------------

        invalid_assembly += int(
            (
                chunk["assembly"]
                != "GRCh38"
            ).sum()
        )

        # ----------------------------------------------
        # DNA allele validation
        # ----------------------------------------------

        reference = (
            chunk[
                "reference_allele"
            ]
            .astype("string")
            .str.upper()
        )

        alternate = (
            chunk[
                "alternate_allele"
            ]
            .astype("string")
            .str.upper()
        )

        valid_bases = {
            "A",
            "C",
            "G",
            "T",
        }

        invalid_reference += int(
            (
                ~reference.isin(
                    valid_bases
                )
            ).sum()
        )

        invalid_alternate += int(
            (
                ~alternate.isin(
                    valid_bases
                )
            ).sum()
        )

        reference_equals_alternate += int(
            (
                reference
                == alternate
            ).sum()
        )

        # ----------------------------------------------
        # Missense verification
        # ----------------------------------------------

        missense_values = (
            chunk[
                "is_missense"
            ]
            .astype("string")
            .str.lower()
        )

        non_missense_rows += int(
            (
                ~missense_values.isin(
                    {
                        "true",
                        "1",
                    }
                )
            ).sum()
        )

        # ----------------------------------------------
        # Amino acids
        # ----------------------------------------------

        reference_aa = (
            chunk[
                "reference_aa"
            ]
            .astype("string")
            .str.upper()
        )

        alternate_aa = (
            chunk[
                "alternate_aa"
            ]
            .astype("string")
            .str.upper()
        )

        invalid_reference_aa += int(
            (
                ~reference_aa.isin(
                    VALID_AMINO_ACIDS
                )
            ).sum()
        )

        invalid_alternate_aa += int(
            (
                ~alternate_aa.isin(
                    VALID_AMINO_ACIDS
                )
            ).sum()
        )

        # ----------------------------------------------
        # Protein positions
        # ----------------------------------------------

        protein_positions = (
            pd.to_numeric(
                chunk[
                    "protein_position"
                ],
                errors="coerce",
            )
        )

        invalid_protein_position += int(
            (
                protein_positions.isna()
                | (
                    protein_positions
                    <= 0
                )
            ).sum()
        )

        # ----------------------------------------------
        # Chromosome validation
        # ----------------------------------------------

        chromosomes = (
            chunk[
                "chromosome"
            ]
            .astype("string")
            .str.upper()
        )

        invalid_chromosome += int(
            (
                ~chromosomes.isin(
                    VALID_CHROMOSOMES
                )
            ).sum()
        )

        # ----------------------------------------------
        # Global duplicate check
        # ----------------------------------------------

        current_keys = (
            chunk[
                "variant_key"
            ]
            .dropna()
            .astype(str)
            .tolist()
        )

        duplicate_variant_keys += sum(
            key in seen_variant_keys
            for key in current_keys
        )

        seen_variant_keys.update(
            current_keys
        )

        # ----------------------------------------------
        # Gene coverage
        # ----------------------------------------------

        current_genes = (
            chunk[
                "gene_symbol"
            ]
            .dropna()
            .astype(str)
            .str.upper()
        )

        genes.update(
            current_genes.tolist()
        )

        for gene in DEMO_GENES:

            demo_gene_counts[
                gene
            ] += int(
                (
                    current_genes
                    == gene
                ).sum()
            )

        # ----------------------------------------------
        # Clinical significance distribution
        # ----------------------------------------------

        significance_counts = (
            chunk[
                "source_clinical_significance"
            ]
            .fillna(
                "MISSING"
            )
            .value_counts()
        )

        for label, count in (
            significance_counts.items()
        ):

            clinical_significance_counts[
                label
            ] = (
                clinical_significance_counts
                .get(
                    label,
                    0,
                )
                + int(count)
            )

    print()

    # --------------------------------------------------
    # Final summary
    # --------------------------------------------------

    print(
        "\n"
        + "=" * 55
    )

    print(
        "VERIFICATION SUMMARY"
    )

    print(
        "=" * 55
    )

    print(
        f"\nTotal rows: "
        f"{total_rows:,}"
    )

    print(
        f"Unique variant keys: "
        f"{len(seen_variant_keys):,}"
    )

    print(
        f"Unique genes: "
        f"{len(genes):,}"
    )

    # --------------------------------------------------
    # Integrity results
    # --------------------------------------------------

    print(
        "\nCritical integrity checks"
    )

    print(
        "-" * 55
    )

    checks = {
        "Missing gene symbols":
            missing_gene_symbol,

        "Missing variant keys":
            missing_variant_key,

        "Duplicate variant keys":
            duplicate_variant_keys,

        "Missing protein changes":
            missing_protein_change,

        "Missing protein positions":
            missing_protein_position,

        "Missing reference amino acids":
            missing_reference_aa,

        "Missing alternate amino acids":
            missing_alternate_aa,

        "Invalid assemblies":
            invalid_assembly,

        "Invalid reference alleles":
            invalid_reference,

        "Invalid alternate alleles":
            invalid_alternate,

        "REF equals ALT":
            reference_equals_alternate,

        "Non-missense rows":
            non_missense_rows,

        "Invalid reference amino acids":
            invalid_reference_aa,

        "Invalid alternate amino acids":
            invalid_alternate_aa,

        "Invalid protein positions":
            invalid_protein_position,

        "Invalid chromosomes":
            invalid_chromosome,
    }

    verification_passed = True

    for name, count in checks.items():

        status = (
            "✅"
            if count == 0
            else "❌"
        )

        print(
            f"{status} "
            f"{name}: "
            f"{count:,}"
        )

        if count != 0:
            verification_passed = False

    # --------------------------------------------------
    # Demo gene coverage
    # --------------------------------------------------

    print(
        "\nDemo gene coverage"
    )

    print(
        "-" * 55
    )

    for gene in sorted(
        DEMO_GENES
    ):

        count = (
            demo_gene_counts[
                gene
            ]
        )

        status = (
            "✅"
            if count > 0
            else "⚠️"
        )

        print(
            f"{status} "
            f"{gene}: "
            f"{count:,} variants"
        )

    # --------------------------------------------------
    # Clinical significance
    # --------------------------------------------------

    print(
        "\nTop clinical significance values"
    )

    print(
        "-" * 55
    )

    sorted_significance = sorted(
        clinical_significance_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    for label, count in (
        sorted_significance[:15]
    ):

        print(
            f"{count:>10,}  {label}"
        )

    # --------------------------------------------------
    # Final result
    # --------------------------------------------------

    print(
        "\n"
        + "=" * 55
    )

    if verification_passed:

        print(
            "✅ SPRINT 2 DATASET VERIFICATION PASSED"
        )

    else:

        print(
            "❌ SPRINT 2 DATASET VERIFICATION FAILED"
        )

        print(
            "Review the failed checks before "
            "continuing to Sprint 3."
        )

    print(
        "=" * 55
    )


if __name__ == "__main__":

    try:

        verify_processed_dataset()

    except Exception as error:

        print(
            "\nVerification failed."
        )

        print(
            f"Error: {error}"
        )

        raise