from pathlib import Path

from config import PROCESSED_DATASET_PATH
from loader import load_clinvar_chunks
from validator import validate_dataframe
from cleaner import clean_clinvar
from normalizer import normalize_clinvar


# Number of ClinVar rows processed at one time
CHUNK_SIZE = 100_000


def prepare_output_file():
    """
    Prepare the processed output file.

    If an older processed dataset exists,
    remove it before starting a new pipeline run.
    """

    PROCESSED_DATASET_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if PROCESSED_DATASET_PATH.exists():

        PROCESSED_DATASET_PATH.unlink()

        print(
            "Old processed dataset removed."
        )


def run_pipeline():
    """
    Run the complete GeneMirror ClinVar
    ingestion and preprocessing pipeline.

    Flow:

    ClinVar raw dataset
        ->
    Loader
        ->
    Validator
        ->
    Cleaner
        ->
    Normalizer
        ->
    Global duplicate removal
        ->
    Processed GeneMirror dataset
    """

    print(
        "GeneMirror Data Processing Pipeline"
    )

    print("-" * 50)

    print(
        f"\nChunk size: {CHUNK_SIZE:,}"
    )

    print(
        f"Output file:"
        f"\n{PROCESSED_DATASET_PATH}"
    )

    # -----------------------------------------
    # Prepare output
    # -----------------------------------------

    prepare_output_file()

    # -----------------------------------------
    # Statistics
    # -----------------------------------------

    total_raw = 0

    total_valid = 0

    total_cleaned = 0

    total_normalized_before_dedup = 0

    total_written = 0

    total_duplicates_removed = 0

    processed_chunks = 0

    # Track all genomic variant keys already written
    # so duplicates across different chunks are removed.
    seen_variant_keys = set()

    first_write = True

    # -----------------------------------------
    # Process ClinVar chunk by chunk
    # -----------------------------------------

    for chunk_number, chunk in enumerate(
        load_clinvar_chunks(
            chunksize=CHUNK_SIZE
        ),
        start=1,
    ):

        print(
            "\n"
            + "=" * 50
        )

        print(
            f"Processing chunk {chunk_number}"
        )

        print(
            "=" * 50
        )

        # -------------------------------------
        # Raw rows
        # -------------------------------------

        raw_count = len(chunk)

        total_raw += raw_count

        print(
            f"Raw rows: "
            f"{raw_count:,}"
        )

        # -------------------------------------
        # Validation
        # -------------------------------------

        validated = validate_dataframe(
            chunk
        )

        valid_count = int(
            validated[
                "validation_passed"
            ].sum()
        )

        total_valid += valid_count

        print(
            f"Rows passing validation: "
            f"{valid_count:,}"
        )

        # -------------------------------------
        # Cleaning
        # -------------------------------------

        cleaned = clean_clinvar(
            validated
        )

        cleaned_count = len(cleaned)

        total_cleaned += cleaned_count

        print(
            f"Missense rows retained: "
            f"{cleaned_count:,}"
        )

        if cleaned.empty:

            print(
                "No supported missense variants "
                "found in this chunk."
            )

            continue

        # -------------------------------------
        # Normalization
        # -------------------------------------

        normalized = normalize_clinvar(
            cleaned
        )

        normalized_count = len(
            normalized
        )

        total_normalized_before_dedup += (
            normalized_count
        )

        print(
            f"Normalized rows: "
            f"{normalized_count:,}"
        )

        # -------------------------------------
        # Global duplicate removal
        # -------------------------------------

        duplicate_mask = (
            normalized[
                "variant_key"
            ].isin(
                seen_variant_keys
            )
        )

        duplicates_in_chunk = int(
            duplicate_mask.sum()
        )

        total_duplicates_removed += (
            duplicates_in_chunk
        )

        normalized = normalized[
            ~duplicate_mask
        ].copy()

        # Add newly accepted variant keys
        # to the global set.
        new_variant_keys = (
            normalized[
                "variant_key"
            ]
            .dropna()
            .tolist()
        )

        seen_variant_keys.update(
            new_variant_keys
        )

        rows_to_write = len(
            normalized
        )

        print(
            f"Cross-chunk duplicates removed: "
            f"{duplicates_in_chunk:,}"
        )

        print(
            f"Rows ready to write: "
            f"{rows_to_write:,}"
        )

        if normalized.empty:

            print(
                "No new unique variants "
                "to write from this chunk."
            )

            continue

        # -------------------------------------
        # Write processed data
        # -------------------------------------

        normalized.to_csv(
            PROCESSED_DATASET_PATH,
            mode=(
                "w"
                if first_write
                else "a"
            ),
            header=first_write,
            index=False,
        )

        first_write = False

        total_written += rows_to_write

        processed_chunks += 1

        print(
            "Chunk written successfully."
        )

    # -----------------------------------------
    # Final pipeline summary
    # -----------------------------------------

    print(
        "\n"
        + "=" * 50
    )

    print(
        "GENEMIRROR PIPELINE COMPLETE"
    )

    print(
        "=" * 50
    )

    print(
        f"\nRaw rows processed: "
        f"{total_raw:,}"
    )

    print(
        f"Rows passing validation: "
        f"{total_valid:,}"
    )

    print(
        f"Missense rows retained: "
        f"{total_cleaned:,}"
    )

    print(
        f"Normalized rows before "
        f"global deduplication: "
        f"{total_normalized_before_dedup:,}"
    )

    print(
        f"Cross-chunk duplicates removed: "
        f"{total_duplicates_removed:,}"
    )

    print(
        f"Final unique variants written: "
        f"{total_written:,}"
    )

    print(
        f"Chunks written: "
        f"{processed_chunks:,}"
    )

    print(
        f"\nProcessed dataset:"
        f"\n{PROCESSED_DATASET_PATH}"
    )

    if PROCESSED_DATASET_PATH.exists():

        file_size_mb = (
            PROCESSED_DATASET_PATH.stat().st_size
            / (1024 ** 2)
        )

        print(
            f"\nProcessed file size: "
            f"{file_size_mb:.2f} MB"
        )

    else:

        print(
            "\nWARNING: Processed dataset "
            "was not created."
        )


if __name__ == "__main__":

    try:

        run_pipeline()

    except KeyboardInterrupt:

        print(
            "\nPipeline interrupted by user."
        )

    except Exception as error:

        print(
            "\nPipeline failed."
        )

        print(
            f"Error: {error}"
        )

        raise