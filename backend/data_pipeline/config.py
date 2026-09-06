from pathlib import Path


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data directories
DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DEMO_DATA_DIR = DATA_DIR / "demo"

# Planned processed dataset
PROCESSED_DATASET_PATH = (
    PROCESSED_DATA_DIR / "genemirror_variants_v1.csv"
)


def ensure_data_directories() -> None:
    """
    Ensure that all GeneMirror data directories exist.
    """

    directories = [
        RAW_DATA_DIR,
        INTERIM_DATA_DIR,
        PROCESSED_DATA_DIR,
        DEMO_DATA_DIR,
    ]

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


if __name__ == "__main__":
    ensure_data_directories()

    print("GeneMirror data directories are ready.")
    print(f"Raw: {RAW_DATA_DIR}")
    print(f"Interim: {INTERIM_DATA_DIR}")
    print(f"Processed: {PROCESSED_DATA_DIR}")
    print(f"Demo: {DEMO_DATA_DIR}")