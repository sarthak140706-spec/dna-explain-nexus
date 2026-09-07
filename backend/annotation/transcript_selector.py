from typing import Any


def is_present(value) -> bool:
    """
    Check whether an annotation field
    contains a meaningful value.
    """

    if value is None:
        return False

    value = str(value).strip()

    return value not in {
        "",
        "None",
        "nan",
        "NA",
    }


def is_canonical(
    transcript: dict[str, Any],
) -> bool:
    """
    Check whether VEP marks a transcript
    as canonical.
    """

    value = transcript.get(
        "canonical"
    )

    return str(value).strip() in {
        "1",
        "true",
        "True",
    }


def is_protein_coding(
    transcript: dict[str, Any],
) -> bool:
    """
    Check whether the transcript biotype
    is protein coding.
    """

    return (
        str(
            transcript.get(
                "biotype",
                ""
            )
        ).strip()
        == "protein_coding"
    )


def is_missense(
    transcript: dict[str, Any],
) -> bool:
    """
    Check whether the transcript has a
    missense consequence.
    """

    return bool(
        transcript.get(
            "is_missense",
            False,
        )
    )


def transcript_selection_score(
    transcript: dict[str, Any],
) -> tuple:
    """
    Generate a deterministic ranking score.

    Priority:
    1. MANE Select
    2. MANE Plus Clinical
    3. Canonical
    4. Protein-coding
    5. Missense
    6. Complete HGVS information
    """

    mane_select = int(
        is_present(
            transcript.get(
                "mane_select"
            )
        )
    )

    mane_plus_clinical = int(
        is_present(
            transcript.get(
                "mane_plus_clinical"
            )
        )
    )

    canonical = int(
        is_canonical(
            transcript
        )
    )

    protein_coding = int(
        is_protein_coding(
            transcript
        )
    )

    missense = int(
        is_missense(
            transcript
        )
    )

    has_hgvsc = int(
        is_present(
            transcript.get(
                "hgvsc"
            )
        )
    )

    has_hgvsp = int(
        is_present(
            transcript.get(
                "hgvsp"
            )
        )
    )

    return (
        mane_select,
        mane_plus_clinical,
        canonical,
        protein_coding,
        missense,
        has_hgvsc,
        has_hgvsp,
    )


def select_best_transcript(
    transcripts: list[dict[str, Any]],
    gene_symbol: str | None = None,
) -> dict[str, Any] | None:
    """
    Select the preferred GeneMirror transcript.

    If gene_symbol is supplied, selection is
    restricted to that gene.
    """

    if not transcripts:
        return None

    candidates = transcripts

    if gene_symbol is not None:

        target_gene = str(
            gene_symbol
        ).strip().upper()

        candidates = [
            transcript
            for transcript in transcripts
            if str(
                transcript.get(
                    "gene_symbol",
                    ""
                )
            ).strip().upper()
            == target_gene
        ]

    if not candidates:
        return None

    # Prefer missense transcripts because
    # GeneMirror V1 currently focuses on
    # missense SNVs.
    missense_candidates = [
        transcript
        for transcript in candidates
        if is_missense(
            transcript
        )
    ]

    if missense_candidates:
        candidates = (
            missense_candidates
        )

    selected = max(
        candidates,
        key=transcript_selection_score,
    )

    return selected


def selection_reason(
    transcript: dict[str, Any] | None,
) -> str:
    """
    Explain why a transcript was selected.
    """

    if transcript is None:
        return "no_transcript_selected"

    reasons = []

    if is_present(
        transcript.get(
            "mane_select"
        )
    ):
        reasons.append(
            "mane_select"
        )

    if is_present(
        transcript.get(
            "mane_plus_clinical"
        )
    ):
        reasons.append(
            "mane_plus_clinical"
        )

    if is_canonical(
        transcript
    ):
        reasons.append(
            "canonical"
        )

    if is_protein_coding(
        transcript
    ):
        reasons.append(
            "protein_coding"
        )

    if is_missense(
        transcript
    ):
        reasons.append(
            "missense"
        )

    if not reasons:
        return "fallback"

    return "|".join(
        reasons
    )


def print_selected_transcript(
    transcript: dict[str, Any] | None,
) -> None:
    """
    Print the selected transcript
    in a compact readable format.
    """

    if transcript is None:

        print(
            "No transcript selected."
        )

        return

    print(
        "\nSelected Transcript"
    )

    print("-" * 60)

    print(
        "Gene:",
        transcript.get(
            "gene_symbol"
        ),
    )

    print(
        "Transcript ID:",
        transcript.get(
            "transcript_id"
        ),
    )

    print(
        "Protein ID:",
        transcript.get(
            "protein_id"
        ),
    )

    print(
        "Biotype:",
        transcript.get(
            "biotype"
        ),
    )

    print(
        "Consequence:",
        transcript.get(
            "consequence_terms"
        ),
    )

    print(
        "HGVSc:",
        transcript.get(
            "hgvsc"
        ),
    )

    print(
        "HGVSp:",
        transcript.get(
            "hgvsp"
        ),
    )

    print(
        "MANE Select:",
        transcript.get(
            "mane_select"
        ),
    )

    print(
        "MANE Plus Clinical:",
        transcript.get(
            "mane_plus_clinical"
        ),
    )

    print(
        "Canonical:",
        transcript.get(
            "canonical"
        ),
    )

    print(
        "Selection reason:",
        selection_reason(
            transcript
        ),
    )


if __name__ == "__main__":

    try:

        from vep_client import (
            annotate_single_variant,
        )

        from parser import (
            parse_vep_result,
        )

        print(
            "GeneMirror Transcript Selector"
        )

        print("-" * 45)

        # TP53 variant from the frozen
        # Sprint 2 GeneMirror dataset.
        raw_result = (
            annotate_single_variant(
                chromosome="17",
                position=7674208,
                reference="A",
                alternate="G",
            )
        )

        parsed_result = (
            parse_vep_result(
                raw_result
            )
        )

        selected = (
            select_best_transcript(
                parsed_result[
                    "transcripts"
                ],
                gene_symbol="TP53",
            )
        )

        print_selected_transcript(
            selected
        )

        print(
            "\nTranscript selector test "
            "completed successfully."
        )

    except Exception as error:

        print(
            "\nTranscript selector test failed."
        )

        print(
            f"Error: {error}"
        )

        raise