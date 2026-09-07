import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from config import (
    ANNOTATION_CACHE_DIR,
    SOURCE_VARIANT_DATASET,
    ANNOTATED_DATASET_PATH,
    ensure_annotation_directories,
)

from annotator import annotate_variant


DEMO_GENES = [
    "TP53",
    "BRCA1",
    "CFTR",
    "HBB",
    "APOE",
    "MTHFR",
]


# ==========================================================
# Cache utilities
# ==========================================================

def build_cache_key(
    chromosome: str,
    position: int,
    reference: str,
    alternate: str,
    gene_symbol: str,
) -> str:

    raw_key = (
        f"{chromosome}:"
        f"{int(position)}:"
        f"{str(reference).upper()}>"
        f"{str(alternate).upper()}:"
        f"{str(gene_symbol).upper()}"
    )

    return hashlib.sha256(
        raw_key.encode("utf-8")
    ).hexdigest()


def get_cache_path(
    chromosome: str,
    position: int,
    reference: str,
    alternate: str,
    gene_symbol: str,
) -> Path:

    cache_key = build_cache_key(
        chromosome=chromosome,
        position=position,
        reference=reference,
        alternate=alternate,
        gene_symbol=gene_symbol,
    )

    return (
        ANNOTATION_CACHE_DIR
        / f"{cache_key}.json"
    )


def load_cached_annotation(
    cache_path: Path,
) -> dict[str, Any] | None:

    if not cache_path.exists():
        return None

    with open(
        cache_path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(
            file
        )


def save_cached_annotation(
    cache_path: Path,
    annotation: dict[str, Any],
) -> None:

    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        cache_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            annotation,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ==========================================================
# Cached annotation
# ==========================================================

def annotate_variant_cached(
    chromosome: str,
    position: int,
    reference: str,
    alternate: str,
    gene_symbol: str,
    source_dna_change: str | None = None,
    source_protein_change: str | None = None,
    use_cache: bool = True,
) -> tuple[dict[str, Any], bool]:

    ensure_annotation_directories()

    cache_path = get_cache_path(
        chromosome=chromosome,
        position=position,
        reference=reference,
        alternate=alternate,
        gene_symbol=gene_symbol,
    )

    if use_cache:

        cached = load_cached_annotation(
            cache_path
        )

        if cached is not None:

            return cached, True

    annotation = annotate_variant(
        chromosome=chromosome,
        position=position,
        reference=reference,
        alternate=alternate,
        gene_symbol=gene_symbol,
        source_dna_change=source_dna_change,
        source_protein_change=source_protein_change,
    )

    save_cached_annotation(
        cache_path,
        annotation,
    )

    return annotation, False


# ==========================================================
# DataFrame annotation
# ==========================================================

def annotate_dataframe(
    dataframe: pd.DataFrame,
    use_cache: bool = True,
) -> pd.DataFrame:

    results = []

    dataframe = dataframe.reset_index(
        drop=True
    )

    total_rows = len(
        dataframe
    )

    for index, row in dataframe.iterrows():

        print(
            f"Annotating "
            f"{index + 1}/{total_rows} | "
            f"{row['gene_symbol']} | "
            f"{row['variant_key']}"
        )

        try:

            annotation, cache_hit = (
                annotate_variant_cached(
                    chromosome=row[
                        "chromosome"
                    ],
                    position=row[
                        "position"
                    ],
                    reference=row[
                        "reference_allele"
                    ],
                    alternate=row[
                        "alternate_allele"
                    ],
                    gene_symbol=row[
                        "gene_symbol"
                    ],
                    source_dna_change=row.get(
                        "dna_change"
                    ),
                    source_protein_change=row.get(
                        "protein_change"
                    ),
                    use_cache=use_cache,
                )
            )

            # Preserve important Sprint 2 metadata

            annotation[
                "variant_key"
            ] = row.get(
                "variant_key"
            )

            annotation[
                "variation_id"
            ] = row.get(
                "variation_id"
            )

            annotation[
                "source_clinical_significance"
            ] = row.get(
                "source_clinical_significance"
            )

            annotation[
                "source_review_status"
            ] = row.get(
                "source_review_status"
            )

            annotation[
                "number_submitters"
            ] = row.get(
                "number_submitters"
            )

            annotation[
                "cache_hit"
            ] = cache_hit

            results.append(
                annotation
            )

        except Exception as error:

            print(
                f"Annotation failed: "
                f"{error}"
            )

            results.append(
                {
                    "variant_key":
                        row.get(
                            "variant_key"
                        ),

                    "variation_id":
                        row.get(
                            "variation_id"
                        ),

                    "gene_symbol":
                        row.get(
                            "gene_symbol"
                        ),

                    "chromosome":
                        row.get(
                            "chromosome"
                        ),

                    "position":
                        row.get(
                            "position"
                        ),

                    "annotation_status":
                        "error",

                    "verification_status":
                        "not_verified",

                    "error_message":
                        str(error),

                    "cache_hit":
                        False,
                }
            )

    return pd.DataFrame(
        results
    )


# ==========================================================
# Demo-gene subset generation
# ==========================================================

def load_demo_gene_variants(
    variants_per_gene: int = 20,
    chunksize: int = 100_000,
) -> pd.DataFrame:
    """
    Read the large Sprint 2 dataset in chunks
    and collect a controlled number of variants
    for each frozen GeneMirror demo gene.
    """

    collected = {
        gene: []
        for gene in DEMO_GENES
    }

    counts = {
        gene: 0
        for gene in DEMO_GENES
    }

    reader = pd.read_csv(
        SOURCE_VARIANT_DATASET,
        chunksize=chunksize,
        low_memory=False,
    )

    for chunk_number, chunk in enumerate(
        reader,
        start=1,
    ):

        print(
            f"Scanning source chunk "
            f"{chunk_number}"
        )

        for gene in DEMO_GENES:

            remaining = (
                variants_per_gene
                - counts[gene]
            )

            if remaining <= 0:
                continue

            matches = chunk[
                chunk[
                    "gene_symbol"
                ]
                == gene
            ]

            if matches.empty:
                continue

            selected = matches.head(
                remaining
            )

            collected[
                gene
            ].append(
                selected
            )

            counts[
                gene
            ] += len(
                selected
            )

        if all(
            counts[gene]
            >= variants_per_gene
            for gene in DEMO_GENES
        ):
            break

    frames = []

    for gene in DEMO_GENES:

        gene_frames = collected[
            gene
        ]

        if not gene_frames:

            continue

        gene_dataframe = pd.concat(
            gene_frames,
            ignore_index=True,
        )

        gene_dataframe = (
            gene_dataframe.head(
                variants_per_gene
            )
        )

        frames.append(
            gene_dataframe
        )

    if not frames:

        raise RuntimeError(
            "No demo-gene variants "
            "were found."
        )

    result = pd.concat(
        frames,
        ignore_index=True,
    )

    return result


# ==========================================================
# Dataset generation
# ==========================================================

def generate_annotated_dataset(
    variants_per_gene: int = 20,
) -> pd.DataFrame:

    ensure_annotation_directories()

    print(
        "\nSelecting GeneMirror "
        "demo-gene variants..."
    )

    source_subset = (
        load_demo_gene_variants(
            variants_per_gene=
                variants_per_gene
        )
    )

    print(
        "\nSelected variants:"
    )

    print(
        source_subset[
            "gene_symbol"
        ].value_counts()
    )

    print(
        f"\nTotal selected: "
        f"{len(source_subset)}"
    )

    print(
        "\nStarting annotation..."
    )

    annotated = annotate_dataframe(
        source_subset,
        use_cache=True,
    )

    # Serialize list-valued consequence
    # fields safely for CSV output.

    if (
        "consequence_terms"
        in annotated.columns
    ):

        annotated[
            "consequence_terms"
        ] = annotated[
            "consequence_terms"
        ].apply(
            lambda value:
                "|".join(value)
                if isinstance(
                    value,
                    list,
                )
                else value
        )

    annotated.to_csv(
        ANNOTATED_DATASET_PATH,
        index=False,
    )

    print(
        "\nAnnotated dataset written:"
    )

    print(
        ANNOTATED_DATASET_PATH
    )

    return annotated


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    print(
        "GeneMirror Annotated "
        "Dataset Generator"
    )

    print("=" * 60)

    annotated = (
        generate_annotated_dataset(
            variants_per_gene=20
        )
    )

    print(
        "\nGeneration Summary"
    )

    print("-" * 60)

    print(
        "Rows:",
        len(
            annotated
        ),
    )

    print(
        "\nGenes:"
    )

    print(
        annotated[
            "gene_symbol"
        ].value_counts()
    )

    print(
        "\nAnnotation status:"
    )

    print(
        annotated[
            "annotation_status"
        ].value_counts(
            dropna=False
        )
    )

    print(
        "\nVerification status:"
    )

    print(
        annotated[
            "verification_status"
        ].value_counts(
            dropna=False
        )
    )

    print(
        "\nCache usage:"
    )

    print(
        annotated[
            "cache_hit"
        ].value_counts(
            dropna=False
        )
    )

    print(
        "\nSprint 3 annotated dataset "
        "generation completed."
    )