from pathlib import Path


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

DATA_DIR = (
    PROJECT_ROOT
    / "data"
)

PROCESSED_DATA_DIR = (
    DATA_DIR
    / "processed"
)

INTERIM_DATA_DIR = (
    DATA_DIR
    / "interim"
)

ANNOTATION_CACHE_DIR = (
    INTERIM_DATA_DIR
    / "annotation_cache"
)


# --------------------------------------------------
# Input / output datasets
# --------------------------------------------------

SOURCE_VARIANT_DATASET = (
    PROCESSED_DATA_DIR
    / "genemirror_variants_v1.csv"
)

ANNOTATED_DATASET_PATH = (
    PROCESSED_DATA_DIR
    / "genemirror_annotated_v1.csv"
)


# --------------------------------------------------
# Ensembl configuration
# --------------------------------------------------

ENSEMBL_REST_SERVER = (
    "https://rest.ensembl.org"
)

ENSEMBL_SPECIES = (
    "homo_sapiens"
)

VEP_REGION_ENDPOINT = (
    f"/vep/{ENSEMBL_SPECIES}/region"
)


# Ensembl currently allows a maximum of
# 200 variants in a VEP POST request.
VEP_BATCH_SIZE = 200


# --------------------------------------------------
# GeneMirror V1 biological scope
# --------------------------------------------------

SUPPORTED_ASSEMBLY = (
    "GRCh38"
)

SUPPORTED_CONSEQUENCE = (
    "missense_variant"
)

SUPPORTED_CHROMOSOMES = {
    *(str(i) for i in range(1, 23)),
    "X",
    "Y",
}


# --------------------------------------------------
# Request settings
# --------------------------------------------------

REQUEST_TIMEOUT_SECONDS = 60

MAX_RETRIES = 3


def ensure_annotation_directories():
    """
    Create directories required by
    the Sprint 3 annotation engine.
    """

    directories = [
        INTERIM_DATA_DIR,
        ANNOTATION_CACHE_DIR,
        PROCESSED_DATA_DIR,
    ]

    for directory in directories:

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


if __name__ == "__main__":

    ensure_annotation_directories()

    print(
        "GeneMirror Annotation Configuration"
    )

    print("-" * 45)

    print(
        f"\nProject root:"
        f"\n{PROJECT_ROOT}"
    )

    print(
        f"\nSource dataset:"
        f"\n{SOURCE_VARIANT_DATASET}"
    )

    print(
        f"\nAnnotation cache:"
        f"\n{ANNOTATION_CACHE_DIR}"
    )

    print(
        f"\nAnnotated dataset:"
        f"\n{ANNOTATED_DATASET_PATH}"
    )

    print(
        f"\nEnsembl REST server:"
        f"\n{ENSEMBL_REST_SERVER}"
    )

    print(
        f"\nVEP endpoint:"
        f"\n{VEP_REGION_ENDPOINT}"
    )

    print(
        f"\nVEP batch size:"
        f"\n{VEP_BATCH_SIZE}"
    )

    print(
        "\nAnnotation configuration ready."
    )