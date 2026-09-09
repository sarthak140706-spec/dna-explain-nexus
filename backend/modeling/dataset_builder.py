import pandas as pd

from config import (
    SOURCE_DATASET_PATH,
    MODELING_DATASET_PATH,
    TARGET_MAPPING,
    TARGET_NAME_MAPPING,
    TARGET_COLUMN,
    TARGET_NAME_COLUMN,
    MODELING_COLUMNS,
    REQUIRED_MODELING_FIELDS,
    CHUNK_SIZE,
    ensure_modeling_directories,
)


# ============================================================
# Target assignment
# ============================================================

def assign_target(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create the Sprint 4 supervised target.

    Target:
        0 = benign-like
        1 = pathogenic-like

    Only exact approved ClinVar classifications
    are retained.
    """

    dataframe = dataframe.copy()

    clinical_significance = (
        dataframe[
            "source_clinical_significance"
        ]
        .astype("string")
        .str.strip()
    )

    dataframe[
        "source_clinical_significance"
    ] = clinical_significance

    dataframe[
        TARGET_COLUMN
    ] = clinical_significance.map(
        TARGET_MAPPING
    )

    dataframe = dataframe[
        dataframe[
            TARGET_COLUMN
        ].notna()
    ].copy()

    dataframe[
        TARGET_COLUMN
    ] = dataframe[
        TARGET_COLUMN
    ].astype(
        "int8"
    )

    dataframe[
        TARGET_NAME_COLUMN
    ] = dataframe[
        TARGET_COLUMN
    ].map(
        TARGET_NAME_MAPPING
    )

    return dataframe


# ============================================================
# Modeling-row validation
# ============================================================

def remove_invalid_rows(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Remove rows that cannot support later
    variant-effect feature engineering.
    """

    dataframe = dataframe.copy()

    missing_schema_fields = [
        column
        for column
        in REQUIRED_MODELING_FIELDS
        if column
        not in dataframe.columns
    ]

    if missing_schema_fields:

        raise KeyError(
            "Required Sprint 2 columns "
            "are missing:\n"
            + "\n".join(
                missing_schema_fields
            )
        )

    # --------------------------------------------------------
    # Remove missing critical values
    # --------------------------------------------------------

    dataframe = dataframe.dropna(
        subset=REQUIRED_MODELING_FIELDS
    ).copy()

    # --------------------------------------------------------
    # Normalize amino-acid fields
    # --------------------------------------------------------

    dataframe[
        "reference_aa"
    ] = (
        dataframe[
            "reference_aa"
        ]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    dataframe[
        "alternate_aa"
    ] = (
        dataframe[
            "alternate_aa"
        ]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # Valid one-letter amino acids

    valid_amino_acids = set(
        "ACDEFGHIKLMNPQRSTVWY"
    )

    valid_reference = (
        dataframe[
            "reference_aa"
        ].isin(
            valid_amino_acids
        )
    )

    valid_alternate = (
        dataframe[
            "alternate_aa"
        ].isin(
            valid_amino_acids
        )
    )

    dataframe = dataframe[
        valid_reference
        & valid_alternate
    ].copy()

    # --------------------------------------------------------
    # Missense substitutions must actually change AA
    # --------------------------------------------------------

    dataframe = dataframe[
        dataframe[
            "reference_aa"
        ]
        != dataframe[
            "alternate_aa"
        ]
    ].copy()

    # --------------------------------------------------------
    # Protein position validation
    # --------------------------------------------------------

    dataframe[
        "protein_position"
    ] = pd.to_numeric(
        dataframe[
            "protein_position"
        ],
        errors="coerce",
    )

    dataframe = dataframe[
        dataframe[
            "protein_position"
        ].notna()
    ].copy()

    dataframe = dataframe[
        dataframe[
            "protein_position"
        ]
        > 0
    ].copy()

    # --------------------------------------------------------
    # Ensure genomic position is numeric and positive
    # --------------------------------------------------------

    dataframe[
        "position"
    ] = pd.to_numeric(
        dataframe[
            "position"
        ],
        errors="coerce",
    )

    dataframe = dataframe[
        dataframe[
            "position"
        ].notna()
    ].copy()

    dataframe = dataframe[
        dataframe[
            "position"
        ]
        > 0
    ].copy()

    # --------------------------------------------------------
    # Final missense flag check
    # --------------------------------------------------------

    if "is_missense" in dataframe.columns:

        missense_values = (
            dataframe[
                "is_missense"
            ]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        dataframe = dataframe[
            missense_values.isin(
                {
                    "true",
                    "1",
                }
            )
        ].copy()

    return dataframe


# ============================================================
# Duplicate handling
# ============================================================

def remove_duplicate_variants(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Remove duplicate genomic variant keys
    within the current chunk.
    """

    dataframe = dataframe.drop_duplicates(
        subset=[
            "variant_key"
        ],
        keep="first",
    )

    return dataframe


# ============================================================
# Column selection
# ============================================================

def select_modeling_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Keep the frozen Sprint 4 modeling schema.
    """

    missing_columns = [
        column
        for column
        in MODELING_COLUMNS
        if column
        not in dataframe.columns
    ]

    if missing_columns:

        print(
            "\nWarning: optional modeling "
            "columns not present:"
        )

        for column in missing_columns:
            print(
                f"  - {column}"
            )

    available_columns = [
        column
        for column
        in MODELING_COLUMNS
        if column
        in dataframe.columns
    ]

    return dataframe[
        available_columns
    ].copy()


# ============================================================
# Main dataset builder
# ============================================================

def build_modeling_dataset():
    """
    Build the Sprint 4 supervised modeling dataset
    from the frozen Sprint 2 variant dataset.

    The source CSV is processed incrementally so the
    full ~706 MB dataset does not need to be loaded
    into memory.
    """

    ensure_modeling_directories()

    if not SOURCE_DATASET_PATH.exists():

        raise FileNotFoundError(
            "Sprint 2 source dataset "
            "was not found:\n"
            f"{SOURCE_DATASET_PATH}"
        )

    if MODELING_DATASET_PATH.exists():

        print(
            "Removing previous modeling dataset..."
        )

        MODELING_DATASET_PATH.unlink()

    # --------------------------------------------------------
    # Global statistics
    # --------------------------------------------------------

    total_source_rows = 0
    total_target_eligible = 0
    total_invalid_removed = 0
    total_duplicates_removed = 0
    total_written = 0

    benign_count = 0
    pathogenic_count = 0

    chunks_written = 0

    # Global deduplication across CSV chunks

    seen_variant_keys = set()

    print(
        "GeneMirror Modeling Dataset Builder"
    )

    print(
        "=" * 65
    )

    print(
        f"\nSource:\n"
        f"{SOURCE_DATASET_PATH}"
    )

    print(
        f"\nOutput:\n"
        f"{MODELING_DATASET_PATH}"
    )

    print(
        "\nBuilding supervised dataset..."
    )

    reader = pd.read_csv(
        SOURCE_DATASET_PATH,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )

    for chunk_number, chunk in enumerate(
        reader,
        start=1,
    ):

        source_rows = len(
            chunk
        )

        total_source_rows += (
            source_rows
        )

        # ====================================================
        # Target assignment
        # ====================================================

        targeted = assign_target(
            chunk
        )

        eligible_rows = len(
            targeted
        )

        total_target_eligible += (
            eligible_rows
        )

        if targeted.empty:

            print(
                f"Chunk {chunk_number:02d} | "
                f"Source: {source_rows:,} | "
                f"Eligible: 0 | "
                f"Written: 0"
            )

            continue

        # ====================================================
        # Critical-field cleaning
        # ====================================================

        cleaned = remove_invalid_rows(
            targeted
        )

        invalid_removed = (
            eligible_rows
            - len(cleaned)
        )

        total_invalid_removed += (
            invalid_removed
        )

        # ====================================================
        # Local duplicate removal
        # ====================================================

        before_local_dedup = len(
            cleaned
        )

        cleaned = remove_duplicate_variants(
            cleaned
        )

        local_duplicates = (
            before_local_dedup
            - len(cleaned)
        )

        # ====================================================
        # Cross-chunk duplicate removal
        # ====================================================

        if not cleaned.empty:

            new_variant_mask = (
                ~cleaned[
                    "variant_key"
                ].isin(
                    seen_variant_keys
                )
            )

            cross_chunk_duplicates = (
                int(
                    (
                        ~new_variant_mask
                    ).sum()
                )
            )

            cleaned = cleaned[
                new_variant_mask
            ].copy()

        else:

            cross_chunk_duplicates = 0

        total_duplicates_removed += (
            local_duplicates
            + cross_chunk_duplicates
        )

        if cleaned.empty:

            print(
                f"Chunk {chunk_number:02d} | "
                f"Source: {source_rows:,} | "
                f"Eligible: {eligible_rows:,} | "
                f"Written: 0"
            )

            continue

        seen_variant_keys.update(
            cleaned[
                "variant_key"
            ].tolist()
        )

        # ====================================================
        # Freeze output columns
        # ====================================================

        cleaned = (
            select_modeling_columns(
                cleaned
            )
        )

        # ====================================================
        # Count classes
        # ====================================================

        class_counts = cleaned[
            TARGET_COLUMN
        ].value_counts()

        chunk_benign = int(
            class_counts.get(
                0,
                0,
            )
        )

        chunk_pathogenic = int(
            class_counts.get(
                1,
                0,
            )
        )

        benign_count += (
            chunk_benign
        )

        pathogenic_count += (
            chunk_pathogenic
        )

        # ====================================================
        # Write incrementally
        # ====================================================

        write_header = (
            chunks_written
            == 0
        )

        cleaned.to_csv(
            MODELING_DATASET_PATH,
            mode=(
                "w"
                if write_header
                else "a"
            ),
            header=write_header,
            index=False,
        )

        written_rows = len(
            cleaned
        )

        total_written += (
            written_rows
        )

        chunks_written += 1

        print(
            f"Chunk {chunk_number:02d} | "
            f"Source: {source_rows:,} | "
            f"Eligible: {eligible_rows:,} | "
            f"Written: {written_rows:,} | "
            f"B: {chunk_benign:,} | "
            f"P: {chunk_pathogenic:,}"
        )

    # ========================================================
    # Final summary
    # ========================================================

    print(
        "\n"
        + "=" * 65
    )

    print(
        "MODELING DATASET SUMMARY"
    )

    print(
        "=" * 65
    )

    print(
        f"\nSource variants examined: "
        f"{total_source_rows:,}"
    )

    print(
        f"Label-eligible variants: "
        f"{total_target_eligible:,}"
    )

    print(
        f"Invalid eligible rows removed: "
        f"{total_invalid_removed:,}"
    )

    print(
        f"Duplicate variants removed: "
        f"{total_duplicates_removed:,}"
    )

    print(
        f"Final modeling variants: "
        f"{total_written:,}"
    )

    print(
        "\nTarget distribution"
    )

    print(
        "-" * 45
    )

    print(
        f"Benign-like (0): "
        f"{benign_count:,}"
    )

    print(
        f"Pathogenic-like (1): "
        f"{pathogenic_count:,}"
    )

    total_classes = (
        benign_count
        + pathogenic_count
    )

    if total_classes > 0:

        benign_percentage = (
            benign_count
            / total_classes
            * 100
        )

        pathogenic_percentage = (
            pathogenic_count
            / total_classes
            * 100
        )

        print(
            f"\nBenign-like percentage: "
            f"{benign_percentage:.2f}%"
        )

        print(
            f"Pathogenic-like percentage: "
            f"{pathogenic_percentage:.2f}%"
        )

        imbalance_ratio = (
            max(
                benign_count,
                pathogenic_count,
            )
            / max(
                1,
                min(
                    benign_count,
                    pathogenic_count,
                ),
            )
        )

        print(
            f"Class imbalance ratio: "
            f"{imbalance_ratio:.2f}:1"
        )

    if MODELING_DATASET_PATH.exists():

        file_size_mb = (
            MODELING_DATASET_PATH
            .stat()
            .st_size
            / (
                1024
                * 1024
            )
        )

        print(
            f"\nOutput file size: "
            f"{file_size_mb:.2f} MB"
        )

    print(
        f"\nOutput:\n"
        f"{MODELING_DATASET_PATH}"
    )

    print(
        "\nImportant:"
    )

    print(
        "ClinVar clinical significance "
        "defined the supervised target."
    )

    print(
        "It must NOT be used as an "
        "input model feature."
    )

    print(
        "\n✅ Sprint 4 modeling dataset "
        "generated successfully."
    )


if __name__ == "__main__":

    build_modeling_dataset()