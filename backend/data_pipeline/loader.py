from pathlib import Path
from typing import Optional

import pandas as pd

from config import RAW_DATA_DIR


CLINVAR_FILE = RAW_DATA_DIR / "variant_summary.txt.gz"


def load_clinvar_chunks(
    file_path: Path = CLINVAR_FILE,
    chunksize: int = 100_000,
):
    """
    Yield ClinVar data in chunks.

    This prevents the entire compressed dataset from being
    loaded into memory at once.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"ClinVar file not found: {file_path}"
        )

    reader = pd.read_csv(
        file_path,
        sep="\t",
        compression="gzip",
        dtype=str,
        low_memory=False,
        chunksize=chunksize,
    )

    for chunk in reader:
        yield chunk


def load_clinvar_sample(
    file_path: Path = CLINVAR_FILE,
    rows: int = 10,
) -> pd.DataFrame:
    """
    Load a small sample from the ClinVar dataset.

    Useful for verifying columns and file structure.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"ClinVar file not found: {file_path}"
        )

    return pd.read_csv(
        file_path,
        sep="\t",
        compression="gzip",
        dtype=str,
        low_memory=False,
        nrows=rows,
    )


def get_clinvar_columns(
    file_path: Path = CLINVAR_FILE,
) -> list[str]:
    """
    Return the column names from the ClinVar dataset
    without loading the full dataset.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"ClinVar file not found: {file_path}"
        )

    header = pd.read_csv(
        file_path,
        sep="\t",
        compression="gzip",
        dtype=str,
        nrows=0,
    )

    return header.columns.tolist()


def count_rows(
    file_path: Path = CLINVAR_FILE,
    chunksize: int = 100_000,
    max_chunks: Optional[int] = None,
) -> int:
    """
    Count rows in the ClinVar dataset using chunked reading.

    max_chunks can be used during testing to avoid reading
    the entire dataset.
    """

    total_rows = 0

    for index, chunk in enumerate(
        load_clinvar_chunks(
            file_path=file_path,
            chunksize=chunksize,
        )
    ):
        total_rows += len(chunk)

        if (
            max_chunks is not None
            and index + 1 >= max_chunks
        ):
            break

    return total_rows


if __name__ == "__main__":

    print("GeneMirror ClinVar Loader")
    print("-" * 40)

    print("\nFile:")
    print(CLINVAR_FILE)

    print("\nColumns:")

    columns = get_clinvar_columns()

    for column in columns:
        print(f"- {column}")

    print(f"\nTotal columns: {len(columns)}")

    print("\nSample records:")

    sample = load_clinvar_sample(
        rows=5
    )

    print(
        sample.head().to_string()
    )

    print("\nTesting chunk loader...")

    first_chunk = next(
        load_clinvar_chunks(
            chunksize=10_000
        )
    )

    print(
        f"First chunk rows: {len(first_chunk)}"
    )

    print(
        f"First chunk columns: "
        f"{len(first_chunk.columns)}"
    )

    print("\nLoader test completed successfully.")