from typing import Any

from vep_client import annotate_single_variant
from parser import parse_vep_result
from transcript_selector import (
    select_best_transcript,
    selection_reason,
)


def strip_hgvs_accession(
    value: str | None,
) -> str | None:
    """
    Remove the transcript/protein accession
    prefix from an HGVS value.

    Examples:

    ENST00000269305.9:c.755T>C
        ->
    c.755T>C

    ENSP00000269305.4:p.Leu252Pro
        ->
    p.Leu252Pro
    """

    if value is None:
        return None

    value = str(
        value
    ).strip()

    if ":" in value:

        return value.split(
            ":",
            1,
        )[1]

    return value


def compare_hgvs(
    expected: str | None,
    observed: str | None,
) -> bool:
    """
    Compare source and VEP HGVS values
    after removing accession prefixes.
    """

    if expected is None:
        return False

    if observed is None:
        return False

    expected = str(
        expected
    ).strip()

    observed = (
        strip_hgvs_accession(
            observed
        )
    )

    return (
        expected
        == observed
    )


def determine_verification_status(
    dna_match: bool,
    protein_match: bool,
) -> str:
    """
    Classify agreement between the
    Sprint 2 source annotation and VEP.

    This is an annotation agreement status,
    not a clinical classification.
    """

    if (
        dna_match
        and protein_match
    ):
        return "full_match"

    if protein_match:
        return "protein_match_only"

    if dna_match:
        return "dna_match_only"

    return "mismatch"


def annotate_variant(
    chromosome: str,
    position: int,
    reference: str,
    alternate: str,
    gene_symbol: str,
    source_dna_change: str | None = None,
    source_protein_change: str | None = None,
) -> dict[str, Any]:
    """
    Annotate one GeneMirror genomic variant
    using Ensembl VEP and select the preferred
    transcript for the requested gene.

    The result also compares the selected
    transcript consequence with the original
    Sprint 2 ClinVar-derived HGVS fields.
    """

    # --------------------------------------------------
    # Request VEP annotation
    # --------------------------------------------------

    raw_result = (
        annotate_single_variant(
            chromosome=chromosome,
            position=position,
            reference=reference,
            alternate=alternate,
        )
    )

    # --------------------------------------------------
    # Parse response
    # --------------------------------------------------

    parsed_result = (
        parse_vep_result(
            raw_result
        )
    )

    # --------------------------------------------------
    # Select transcript for source gene
    # --------------------------------------------------

    selected = (
        select_best_transcript(
            parsed_result.get(
                "transcripts",
                []
            ),
            gene_symbol=gene_symbol,
        )
    )

    if selected is None:

        return {
            "annotation_status":
                "no_transcript_found",

            "gene_symbol":
                gene_symbol,

            "chromosome":
                str(chromosome),

            "position":
                int(position),

            "reference_allele":
                str(reference).upper(),

            "alternate_allele":
                str(alternate).upper(),

            "source_dna_change":
                source_dna_change,

            "source_protein_change":
                source_protein_change,

            "most_severe_consequence":
                parsed_result.get(
                    "most_severe_consequence"
                ),

            "transcript_id":
                None,

            "mane_select":
                None,

            "canonical":
                None,

            "vep_hgvsc":
                None,

            "vep_hgvsp":
                None,

            "vep_dna_change":
                None,

            "vep_protein_change":
                None,

            "dna_match":
                False,

            "protein_match":
                False,

            "verification_status":
                "not_verified",

            "selection_reason":
                "no_transcript_selected",
        }

    # --------------------------------------------------
    # Extract selected consequence
    # --------------------------------------------------

    vep_hgvsc = (
        selected.get(
            "hgvsc"
        )
    )

    vep_hgvsp = (
        selected.get(
            "hgvsp"
        )
    )

    vep_dna_change = (
        strip_hgvs_accession(
            vep_hgvsc
        )
    )

    vep_protein_change = (
        strip_hgvs_accession(
            vep_hgvsp
        )
    )

    # --------------------------------------------------
    # Compare with Sprint 2
    # --------------------------------------------------

    dna_match = (
        compare_hgvs(
            source_dna_change,
            vep_hgvsc,
        )
        if source_dna_change is not None
        else False
    )

    protein_match = (
        compare_hgvs(
            source_protein_change,
            vep_hgvsp,
        )
        if source_protein_change is not None
        else False
    )

    verification_status = (
        determine_verification_status(
            dna_match=dna_match,
            protein_match=protein_match,
        )
    )

    # --------------------------------------------------
    # GeneMirror annotation output
    # --------------------------------------------------

    return {
        "annotation_status":
            "annotated",

        "gene_symbol":
            gene_symbol,

        "chromosome":
            str(chromosome),

        "position":
            int(position),

        "reference_allele":
            str(reference).upper(),

        "alternate_allele":
            str(alternate).upper(),

        "source_dna_change":
            source_dna_change,

        "source_protein_change":
            source_protein_change,

        "most_severe_consequence":
            parsed_result.get(
                "most_severe_consequence"
            ),

        "transcript_id":
            selected.get(
                "transcript_id"
            ),

        "gene_id":
            selected.get(
                "gene_id"
            ),

        "biotype":
            selected.get(
                "biotype"
            ),

        "consequence_terms":
            selected.get(
                "consequence_terms"
            ),

        "is_missense":
            selected.get(
                "is_missense"
            ),

        "mane_select":
            selected.get(
                "mane_select"
            ),

        "mane_plus_clinical":
            selected.get(
                "mane_plus_clinical"
            ),

        "canonical":
            selected.get(
                "canonical"
            ),

        "strand":
            selected.get(
                "strand"
            ),

        "protein_start":
            selected.get(
                "protein_start"
            ),

        "amino_acids":
            selected.get(
                "amino_acids"
            ),

        "codons":
            selected.get(
                "codons"
            ),

        "vep_hgvsc":
            vep_hgvsc,

        "vep_hgvsp":
            vep_hgvsp,

        "vep_dna_change":
            vep_dna_change,

        "vep_protein_change":
            vep_protein_change,

        "dna_match":
            dna_match,

        "protein_match":
            protein_match,

        "verification_status":
            verification_status,

        "selection_reason":
            selection_reason(
                selected
            ),

        "total_transcript_count":
            parsed_result.get(
                "transcript_count"
            ),

        "missense_transcript_count":
            parsed_result.get(
                "missense_transcript_count"
            ),
    }


def print_annotation(
    result: dict[str, Any],
) -> None:
    """
    Print a compact GeneMirror
    annotation verification result.
    """

    print(
        "\nGeneMirror Variant Annotation"
    )

    print("-" * 60)

    print(
        "Gene:",
        result.get(
            "gene_symbol"
        ),
    )

    print(
        "Genomic variant:",
        (
            f"chr"
            f"{result.get('chromosome')}:"
            f"{result.get('position')}:"
            f"{result.get('reference_allele')}>"
            f"{result.get('alternate_allele')}"
        ),
    )

    print(
        "\nSelected transcript:",
        result.get(
            "transcript_id"
        ),
    )

    print(
        "MANE Select:",
        result.get(
            "mane_select"
        ),
    )

    print(
        "Canonical:",
        result.get(
            "canonical"
        ),
    )

    print(
        "Consequence:",
        result.get(
            "consequence_terms"
        ),
    )

    print(
        "\nSprint 2 DNA change:",
        result.get(
            "source_dna_change"
        ),
    )

    print(
        "VEP DNA change:",
        result.get(
            "vep_dna_change"
        ),
    )

    print(
        "DNA match:",
        result.get(
            "dna_match"
        ),
    )

    print(
        "\nSprint 2 protein change:",
        result.get(
            "source_protein_change"
        ),
    )

    print(
        "VEP protein change:",
        result.get(
            "vep_protein_change"
        ),
    )

    print(
        "Protein match:",
        result.get(
            "protein_match"
        ),
    )

    print(
        "\nVerification status:",
        result.get(
            "verification_status"
        ),
    )

    print(
        "Selection reason:",
        result.get(
            "selection_reason"
        ),
    )


if __name__ == "__main__":

    try:

        print(
            "GeneMirror Missense "
            "Consequence Verification"
        )

        print("=" * 60)

        # Actual TP53 record from the
        # frozen Sprint 2 dataset.
        result = annotate_variant(
            chromosome="17",
            position=7674208,
            reference="A",
            alternate="G",
            gene_symbol="TP53",
            source_dna_change="c.755T>C",
            source_protein_change="p.Leu252Pro",
        )

        print_annotation(
            result
        )

        print(
            "\nMissense consequence verification "
            "test completed successfully."
        )

    except Exception as error:

        print(
            "\nMissense consequence "
            "verification failed."
        )

        print(
            f"Error: {error}"
        )

        raise