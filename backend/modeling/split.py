import pandas as pd

from sklearn.model_selection import StratifiedGroupKFold

from config import (
    FEATURE_DATASET_PATH,
    TRAIN_DATASET_PATH,
    VALIDATION_DATASET_PATH,
    TEST_DATASET_PATH,
    SPLIT_RANDOM_SEED,
)


# ============================================================
# Split configuration
# ============================================================

N_SPLITS = 20

TRAIN_FOLDS = set(range(0, 14))
VALIDATION_FOLDS = set(range(14, 17))
TEST_FOLDS = set(range(17, 20))


# ============================================================
# Source validation
# ============================================================

def validate_source_dataset(
    dataframe: pd.DataFrame,
):
    """
    Validate the Sprint 4 feature dataset before
    gene-aware stratified splitting.
    """

    required_columns = [
        "variant_key",
        "gene_symbol",
        "target_label",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:

        raise KeyError(
            "Required columns missing:\n"
            + "\n".join(missing_columns)
        )

    if dataframe["variant_key"].isna().any():

        raise ValueError(
            "Missing variant keys detected."
        )

    if dataframe["gene_symbol"].isna().any():

        raise ValueError(
            "Missing gene symbols detected."
        )

    if dataframe["target_label"].isna().any():

        raise ValueError(
            "Missing target labels detected."
        )

    duplicate_variants = int(
        dataframe[
            "variant_key"
        ]
        .duplicated()
        .sum()
    )

    if duplicate_variants != 0:

        raise ValueError(
            f"{duplicate_variants} duplicate "
            "variant keys detected."
        )

    targets = set(
        dataframe[
            "target_label"
        ]
        .astype(int)
        .unique()
    )

    if targets != {0, 1}:

        raise ValueError(
            f"Unexpected target classes: "
            f"{targets}"
        )


# ============================================================
# Build stratified group folds
# ============================================================

def assign_stratified_group_folds(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assign each row to one of 20 folds while:

    1. keeping every gene entirely inside one fold
    2. approximately preserving class proportions
    3. approximately balancing fold sizes
    """

    dataframe = dataframe.copy()

    dataframe[
        "split_fold"
    ] = -1

    splitter = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=SPLIT_RANDOM_SEED,
    )

    X = dataframe[
        [
            "variant_key"
        ]
    ]

    y = dataframe[
        "target_label"
    ].astype(int)

    groups = dataframe[
        "gene_symbol"
    ]

    for fold_number, (
        _,
        fold_indices,
    ) in enumerate(
        splitter.split(
            X,
            y,
            groups,
        )
    ):

        dataframe.loc[
            dataframe.index[
                fold_indices
            ],
            "split_fold",
        ] = fold_number

    if (
        dataframe[
            "split_fold"
        ]
        == -1
    ).any():

        raise RuntimeError(
            "Some rows were not assigned "
            "to a split fold."
        )

    return dataframe


# ============================================================
# Convert folds into final datasets
# ============================================================

def create_final_splits(
    dataframe: pd.DataFrame,
):
    """
    Combine the 20 folds into:

        14 train folds
         3 validation folds
         3 test folds
    """

    train = dataframe[
        dataframe[
            "split_fold"
        ].isin(
            TRAIN_FOLDS
        )
    ].copy()

    validation = dataframe[
        dataframe[
            "split_fold"
        ].isin(
            VALIDATION_FOLDS
        )
    ].copy()

    test = dataframe[
        dataframe[
            "split_fold"
        ].isin(
            TEST_FOLDS
        )
    ].copy()

    return (
        train,
        validation,
        test,
    )


# ============================================================
# Leakage verification
# ============================================================

def verify_no_leakage(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
):
    """
    Verify zero gene and variant leakage.
    """

    train_genes = set(
        train[
            "gene_symbol"
        ]
    )

    validation_genes = set(
        validation[
            "gene_symbol"
        ]
    )

    test_genes = set(
        test[
            "gene_symbol"
        ]
    )

    train_validation_gene_overlap = (
        train_genes
        & validation_genes
    )

    train_test_gene_overlap = (
        train_genes
        & test_genes
    )

    validation_test_gene_overlap = (
        validation_genes
        & test_genes
    )

    if train_validation_gene_overlap:

        raise RuntimeError(
            "Gene leakage between "
            "train and validation."
        )

    if train_test_gene_overlap:

        raise RuntimeError(
            "Gene leakage between "
            "train and test."
        )

    if validation_test_gene_overlap:

        raise RuntimeError(
            "Gene leakage between "
            "validation and test."
        )

    train_variants = set(
        train[
            "variant_key"
        ]
    )

    validation_variants = set(
        validation[
            "variant_key"
        ]
    )

    test_variants = set(
        test[
            "variant_key"
        ]
    )

    if (
        train_variants
        & validation_variants
    ):

        raise RuntimeError(
            "Variant leakage between "
            "train and validation."
        )

    if (
        train_variants
        & test_variants
    ):

        raise RuntimeError(
            "Variant leakage between "
            "train and test."
        )

    if (
        validation_variants
        & test_variants
    ):

        raise RuntimeError(
            "Variant leakage between "
            "validation and test."
        )


# ============================================================
# Class verification
# ============================================================

def verify_classes(
    dataframe: pd.DataFrame,
    split_name: str,
):
    """
    Ensure both supervised classes occur
    in every final split.
    """

    classes = set(
        dataframe[
            "target_label"
        ]
        .astype(int)
        .unique()
    )

    if classes != {0, 1}:

        raise RuntimeError(
            f"{split_name} does not "
            "contain both classes."
        )


# ============================================================
# Summary utilities
# ============================================================

def get_split_statistics(
    dataframe: pd.DataFrame,
    total_rows: int,
):
    """
    Return summary statistics for a split.
    """

    rows = len(
        dataframe
    )

    genes = int(
        dataframe[
            "gene_symbol"
        ]
        .nunique()
    )

    benign = int(
        (
            dataframe[
                "target_label"
            ]
            == 0
        ).sum()
    )

    pathogenic = int(
        (
            dataframe[
                "target_label"
            ]
            == 1
        ).sum()
    )

    row_percentage = (
        rows
        / total_rows
        * 100
        if total_rows
        else 0
    )

    pathogenic_percentage = (
        pathogenic
        / rows
        * 100
        if rows
        else 0
    )

    return {
        "rows": rows,
        "genes": genes,
        "benign": benign,
        "pathogenic": pathogenic,
        "row_percentage": row_percentage,
        "pathogenic_percentage": (
            pathogenic_percentage
        ),
    }


def print_split_summary(
    name: str,
    dataframe: pd.DataFrame,
    total_rows: int,
):
    """
    Display one split summary.
    """

    stats = get_split_statistics(
        dataframe,
        total_rows,
    )

    print(
        f"\n{name}"
    )

    print(
        "-" * 60
    )

    print(
        f"Rows: "
        f"{stats['rows']:,} "
        f"({stats['row_percentage']:.2f}%)"
    )

    print(
        f"Genes: "
        f"{stats['genes']:,}"
    )

    print(
        f"Benign-like: "
        f"{stats['benign']:,}"
    )

    print(
        f"Pathogenic-like: "
        f"{stats['pathogenic']:,}"
    )

    print(
        f"Pathogenic percentage: "
        f"{stats['pathogenic_percentage']:.2f}%"
    )


# ============================================================
# Fold-level diagnostics
# ============================================================

def print_fold_summary(
    dataframe: pd.DataFrame,
):
    """
    Print the row and class distribution of
    all 20 internal folds.
    """

    print(
        "\nInternal fold distribution"
    )

    print(
        "-" * 60
    )

    print(
        "Fold | Rows | Genes | Pathogenic %"
    )

    print(
        "-" * 60
    )

    for fold_number in range(
        N_SPLITS
    ):

        fold = dataframe[
            dataframe[
                "split_fold"
            ]
            == fold_number
        ]

        rows = len(
            fold
        )

        genes = fold[
            "gene_symbol"
        ].nunique()

        pathogenic_percentage = (
            (
                fold[
                    "target_label"
                ]
                == 1
            ).mean()
            * 100
        )

        print(
            f"{fold_number:>4} | "
            f"{rows:>6,} | "
            f"{genes:>5,} | "
            f"{pathogenic_percentage:>10.2f}%"
        )


# ============================================================
# Main pipeline
# ============================================================

def build_splits():

    if not FEATURE_DATASET_PATH.exists():

        raise FileNotFoundError(
            "Feature dataset not found:\n"
            f"{FEATURE_DATASET_PATH}"
        )

    print(
        "GeneMirror Stratified "
        "Gene-Aware Dataset Split"
    )

    print(
        "=" * 65
    )

    print(
        f"\nInput:\n"
        f"{FEATURE_DATASET_PATH}"
    )

    dataframe = pd.read_csv(
        FEATURE_DATASET_PATH,
        low_memory=False,
    )

    print(
        f"\nRows loaded: "
        f"{len(dataframe):,}"
    )

    print(
        f"Unique genes: "
        f"{dataframe['gene_symbol'].nunique():,}"
    )

    overall_pathogenic_percentage = (
        (
            dataframe[
                "target_label"
            ]
            == 1
        ).mean()
        * 100
    )

    print(
        f"Overall pathogenic percentage: "
        f"{overall_pathogenic_percentage:.2f}%"
    )

    validate_source_dataset(
        dataframe
    )

    # ========================================================
    # Generate 20 stratified gene-aware folds
    # ========================================================

    dataframe = (
        assign_stratified_group_folds(
            dataframe
        )
    )

    print_fold_summary(
        dataframe
    )

    # ========================================================
    # Convert folds into 70 / 15 / 15 split
    # ========================================================

    (
        train,
        validation,
        test,
    ) = create_final_splits(
        dataframe
    )

    # ========================================================
    # Integrity verification
    # ========================================================

    verify_no_leakage(
        train,
        validation,
        test,
    )

    verify_classes(
        train,
        "Train",
    )

    verify_classes(
        validation,
        "Validation",
    )

    verify_classes(
        test,
        "Test",
    )

    assigned_rows = (
        len(train)
        + len(validation)
        + len(test)
    )

    if assigned_rows != len(
        dataframe
    ):

        raise RuntimeError(
            "Final split row total "
            "does not equal source row total."
        )

    # ========================================================
    # Remove internal fold marker before model datasets
    # ========================================================

    train = train.drop(
        columns=[
            "split_fold"
        ]
    )

    validation = validation.drop(
        columns=[
            "split_fold"
        ]
    )

    test = test.drop(
        columns=[
            "split_fold"
        ]
    )

    # ========================================================
    # Write datasets
    # ========================================================

    train.to_csv(
        TRAIN_DATASET_PATH,
        index=False,
    )

    validation.to_csv(
        VALIDATION_DATASET_PATH,
        index=False,
    )

    test.to_csv(
        TEST_DATASET_PATH,
        index=False,
    )

    # ========================================================
    # Final report
    # ========================================================

    print(
        "\n"
        + "=" * 65
    )

    print(
        "FINAL SPLIT SUMMARY"
    )

    print(
        "=" * 65
    )

    total_rows = len(
        dataframe
    )

    print_split_summary(
        "TRAIN",
        train,
        total_rows,
    )

    print_split_summary(
        "VALIDATION",
        validation,
        total_rows,
    )

    print_split_summary(
        "TEST",
        test,
        total_rows,
    )

    print(
        "\nLeakage checks"
    )

    print(
        "-" * 60
    )

    print(
        "✅ Train/validation gene overlap: 0"
    )

    print(
        "✅ Train/test gene overlap: 0"
    )

    print(
        "✅ Validation/test gene overlap: 0"
    )

    print(
        "✅ Variant overlap across splits: 0"
    )

    print(
        "\nDesired proportions"
    )

    print(
        "-" * 60
    )

    print(
        "Train:      approximately 70%"
    )

    print(
        "Validation: approximately 15%"
    )

    print(
        "Test:       approximately 15%"
    )

    print(
        f"\nTrain output:\n"
        f"{TRAIN_DATASET_PATH}"
    )

    print(
        f"\nValidation output:\n"
        f"{VALIDATION_DATASET_PATH}"
    )

    print(
        f"\nTest output:\n"
        f"{TEST_DATASET_PATH}"
    )

    print(
        "\n✅ Sprint 4 stratified "
        "gene-aware split completed."
    )


if __name__ == "__main__":

    build_splits()