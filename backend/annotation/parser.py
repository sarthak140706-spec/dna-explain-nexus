from typing import Any


def parse_consequence_terms(
    consequence_terms,
) -> list[str]:
    """
    Normalize VEP consequence terms
    into a list of strings.
    """

    if consequence_terms is None:
        return []

    if isinstance(
        consequence_terms,
        list,
    ):
        return [
            str(term)
            for term in consequence_terms
        ]

    return [
        str(consequence_terms)
    ]


def contains_missense(
    consequence_terms,
) -> bool:
    """
    Check whether transcript consequences
    include a missense variant.
    """

    terms = parse_consequence_terms(
        consequence_terms
    )

    return (
        "missense_variant"
        in terms
    )


def parse_transcript_consequence(
    transcript: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert one raw Ensembl VEP transcript
    consequence into GeneMirror's internal
    transcript annotation structure.
    """

    consequence_terms = (
        parse_consequence_terms(
            transcript.get(
                "consequence_terms"
            )
        )
    )

    return {
        "gene_symbol":
            transcript.get(
                "gene_symbol"
            ),

        "gene_id":
            transcript.get(
                "gene_id"
            ),

        "transcript_id":
            transcript.get(
                "transcript_id"
            ),

        "protein_id":
            transcript.get(
                "protein_id"
            ),

        "biotype":
            transcript.get(
                "biotype"
            ),

        "consequence_terms":
            consequence_terms,

        "is_missense":
            contains_missense(
                consequence_terms
            ),

        "hgvsc":
            transcript.get(
                "hgvsc"
            ),

        "hgvsp":
            transcript.get(
                "hgvsp"
            ),

        "cdna_start":
            transcript.get(
                "cdna_start"
            ),

        "cdna_end":
            transcript.get(
                "cdna_end"
            ),

        "cds_start":
            transcript.get(
                "cds_start"
            ),

        "cds_end":
            transcript.get(
                "cds_end"
            ),

        "protein_start":
            transcript.get(
                "protein_start"
            ),

        "protein_end":
            transcript.get(
                "protein_end"
            ),

        "amino_acids":
            transcript.get(
                "amino_acids"
            ),

        "codons":
            transcript.get(
                "codons"
            ),

        "strand":
            transcript.get(
                "strand"
            ),

        "canonical":
            transcript.get(
                "canonical"
            ),

        "mane_select":
            transcript.get(
                "mane_select"
            ),

        "mane_plus_clinical":
            transcript.get(
                "mane_plus_clinical"
            ),

        "tsl":
            transcript.get(
                "tsl"
            ),

        "appris":
            transcript.get(
                "appris"
            ),

        "transcript_support_level":
            transcript.get(
                "transcript_support_level"
            ),
    }


def parse_vep_result(
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert one complete VEP variant result
    into GeneMirror's variant-level annotation
    structure while preserving every
    transcript consequence.
    """

    raw_transcripts = (
        result.get(
            "transcript_consequences",
            []
        )
    )

    parsed_transcripts = [
        parse_transcript_consequence(
            transcript
        )
        for transcript
        in raw_transcripts
    ]

    return {
        "input":
            result.get(
                "input"
            ),

        "assembly_name":
            result.get(
                "assembly_name"
            ),

        "seq_region_name":
            result.get(
                "seq_region_name"
            ),

        "start":
            result.get(
                "start"
            ),

        "end":
            result.get(
                "end"
            ),

        "strand":
            result.get(
                "strand"
            ),

        "allele_string":
            result.get(
                "allele_string"
            ),

        "most_severe_consequence":
            result.get(
                "most_severe_consequence"
            ),

        "transcript_count":
            len(
                parsed_transcripts
            ),

        "missense_transcript_count":
            sum(
                transcript[
                    "is_missense"
                ]
                for transcript
                in parsed_transcripts
            ),

        "transcripts":
            parsed_transcripts,
    }


def get_transcripts_for_gene(
    parsed_result: dict[str, Any],
    gene_symbol: str,
) -> list[dict[str, Any]]:
    """
    Return transcript consequences belonging
    to one gene symbol.
    """

    target_gene = str(
        gene_symbol
    ).strip().upper()

    return [
        transcript
        for transcript
        in parsed_result.get(
            "transcripts",
            []
        )
        if str(
            transcript.get(
                "gene_symbol",
                ""
            )
        ).strip().upper()
        == target_gene
    ]


def get_missense_transcripts(
    parsed_result: dict[str, Any],
    gene_symbol: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return transcript annotations whose
    consequence includes missense_variant.

    Optionally restrict results to one gene.
    """

    transcripts = (
        parsed_result.get(
            "transcripts",
            []
        )
    )

    if gene_symbol is not None:

        target_gene = str(
            gene_symbol
        ).strip().upper()

        transcripts = [
            transcript
            for transcript
            in transcripts
            if str(
                transcript.get(
                    "gene_symbol",
                    ""
                )
            ).strip().upper()
            == target_gene
        ]

    return [
        transcript
        for transcript
        in transcripts
        if transcript.get(
            "is_missense"
        )
    ]


def print_transcript_summary(
    transcripts: list[dict[str, Any]],
    limit: int = 20,
) -> None:
    """
    Print a compact transcript summary
    for development and verification.
    """

    print(
        "\nTranscript Summary"
    )

    print("-" * 100)

    if not transcripts:

        print(
            "No transcripts found."
        )

        return

    for transcript in (
        transcripts[:limit]
    ):

        consequences = ",".join(
            transcript.get(
                "consequence_terms",
                []
            )
        )

        print(
            f"Gene: "
            f"{transcript.get('gene_symbol')} "
            f"| Transcript: "
            f"{transcript.get('transcript_id')} "
            f"| Consequence: "
            f"{consequences} "
            f"| HGVSc: "
            f"{transcript.get('hgvsc')} "
            f"| HGVSp: "
            f"{transcript.get('hgvsp')} "
            f"| MANE: "
            f"{transcript.get('mane_select')} "
            f"| Canonical: "
            f"{transcript.get('canonical')}"
        )


if __name__ == "__main__":

    try:

        from vep_client import (
            annotate_single_variant,
        )

        print(
            "GeneMirror Transcript Parser"
        )

        print("-" * 45)

        # Actual TP53 variant from the
        # frozen Sprint 2 dataset.
        raw_result = (
            annotate_single_variant(
                chromosome="17",
                position=7674208,
                reference="A",
                alternate="G",
            )
        )

        parsed = parse_vep_result(
            raw_result
        )

        print(
            f"\nInput: "
            f"{parsed['input']}"
        )

        print(
            f"Assembly: "
            f"{parsed['assembly_name']}"
        )

        print(
            f"Most severe consequence: "
            f"{parsed['most_severe_consequence']}"
        )

        print(
            f"Total transcripts: "
            f"{parsed['transcript_count']}"
        )

        print(
            f"Missense transcripts: "
            f"{parsed['missense_transcript_count']}"
        )

        tp53_transcripts = (
            get_transcripts_for_gene(
                parsed,
                "TP53",
            )
        )

        print(
            f"TP53 transcripts: "
            f"{len(tp53_transcripts)}"
        )

        tp53_missense = (
            get_missense_transcripts(
                parsed,
                gene_symbol="TP53",
            )
        )

        print(
            f"TP53 missense transcripts: "
            f"{len(tp53_missense)}"
        )

        print_transcript_summary(
            tp53_missense,
            limit=20,
        )

        print(
            "\nTranscript parser test "
            "completed successfully."
        )

    except Exception as error:

        print(
            "\nTranscript parser test failed."
        )

        print(
            f"Error: {error}"
        )

        raise