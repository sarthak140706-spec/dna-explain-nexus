from pathlib import Path


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

SOURCE_DATASET_PATH = (
    PROCESSED_DATA_DIR
    / "genemirror_variants_v1.csv"
)

MODELING_DATASET_PATH = (
    PROCESSED_DATA_DIR
    / "genemirror_modeling_v1.csv"
)

FEATURE_DATASET_PATH = (
    PROCESSED_DATA_DIR
    / "genemirror_features_v1.csv"
)

TRAIN_DATASET_PATH = (
    PROCESSED_DATA_DIR
    / "genemirror_train_v1.csv"
)

VALIDATION_DATASET_PATH = (
    PROCESSED_DATA_DIR
    / "genemirror_validation_v1.csv"
)

TEST_DATASET_PATH = (
    PROCESSED_DATA_DIR
    / "genemirror_test_v1.csv"
)


TRAIN_FRACTION = 0.70
VALIDATION_FRACTION = 0.15
TEST_FRACTION = 0.15

SPLIT_RANDOM_SEED = 42


# ============================================================
# Sprint 4 target definition
# ============================================================

TARGET_COLUMN = "target_label"
TARGET_NAME_COLUMN = "target_name"


BENIGN_LABELS = {
    "Benign",
    "Likely benign",
    "Benign/Likely benign",
}


PATHOGENIC_LABELS = {
    "Pathogenic",
    "Likely pathogenic",
    "Pathogenic/Likely pathogenic",
}


TARGET_MAPPING = {
    "Benign": 0,
    "Likely benign": 0,
    "Benign/Likely benign": 0,

    "Pathogenic": 1,
    "Likely pathogenic": 1,
    "Pathogenic/Likely pathogenic": 1,
}


TARGET_NAME_MAPPING = {
    0: "benign_like",
    1: "pathogenic_like",
}


# ============================================================
# Dataset processing
# ============================================================

CHUNK_SIZE = 100_000


# ============================================================
# Columns retained for Sprint 4
# ============================================================

MODELING_COLUMNS = [
    "allele_id",
    "variation_id",
    "gene_id",
    "gene_symbol",
    "hgnc_id",

    "chromosome",
    "position",
    "reference_allele",
    "alternate_allele",

    "dna_change",
    "protein_change",
    "is_missense",

    "reference_aa_3",
    "alternate_aa_3",
    "reference_aa",
    "alternate_aa",
    "protein_position",
    "amino_acid_change",

    "variant_key",

    # --------------------------------------------------------
    # Source metadata retained for traceability only.
    # Do NOT automatically use these as predictive features.
    # --------------------------------------------------------

    "source_clinical_significance",
    "source_clinsig_simple",
    "review_status",
    "number_submitters",

    TARGET_COLUMN,
    TARGET_NAME_COLUMN,
]


# ============================================================
# Critical fields required for model-building rows
# ============================================================

REQUIRED_MODELING_FIELDS = [
    "gene_symbol",
    "chromosome",
    "position",
    "reference_allele",
    "alternate_allele",
    "protein_change",
    "reference_aa",
    "alternate_aa",
    "protein_position",
    "amino_acid_change",
    "variant_key",
]


def ensure_modeling_directories():
    """
    Ensure Sprint 4 data directories exist.
    """

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


if __name__ == "__main__":

    ensure_modeling_directories()

    print(
        "GeneMirror Modeling Configuration"
    )

    print(
        "=" * 60
    )

    print(
        f"\nProject root:\n"
        f"{PROJECT_ROOT}"
    )

    print(
        f"\nSprint 2 source dataset:\n"
        f"{SOURCE_DATASET_PATH}"
    )

    print(
        f"\nSprint 4 modeling dataset:\n"
        f"{MODELING_DATASET_PATH}"
    )

    print(
        "\nBenign-like target labels:"
    )

    for label in sorted(
        BENIGN_LABELS
    ):
        print(
            f"  0 -> {label}"
        )

    print(
        "\nPathogenic-like target labels:"
    )

    for label in sorted(
        PATHOGENIC_LABELS
    ):
        print(
            f"  1 -> {label}"
        )

    print(
        "\nTarget policy:"
    )

    print(
        "  Only exact approved ClinVar "
        "classifications are used."
    )

    print(
        "  VUS, conflicting, risk-factor, "
        "association and composite labels "
        "are excluded."
    )

    print(
        "\nModeling configuration ready."
    )