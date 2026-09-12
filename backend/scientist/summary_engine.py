import sys
from pathlib import Path
from typing import List


# ============================================================
# Make project root importable
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# Imports
# ============================================================

from backend.scientist.config import (
    CONFIDENCE_INTERPRETATION,
    PREDICTION_INTERPRETATION,
    PROTEIN_CONTEXT_INTERPRETATION,
    XAI_INTERPRETATION,
)

from backend.scientist.contracts import (
    GroundedEvidence,
    ScientistExplanationSections,
    ScientistInput,
    ScientistOutput,
    validate_scientist_input,
    validate_scientist_output,
)

from backend.scientist.evidence_builder import (
    build_grounded_evidence,
    verify_grounded_evidence,
)


# ============================================================
# Helpers
# ============================================================

def evidence_by_category(
    evidence: List[GroundedEvidence],
    categories,
) -> List[GroundedEvidence]:

    category_set = set(categories)

    return [
        item
        for item in evidence
        if item.category in category_set
    ]


def join_statements(
    evidence: List[GroundedEvidence],
) -> str:

    return " ".join(
        item.statement
        for item in evidence
        if item.statement.strip()
    )


# ============================================================
# Overview section
# ============================================================

def build_overview_section(
    scientist_input: ScientistInput,
) -> str:

    variant = scientist_input.variant
    prediction = scientist_input.prediction

    if variant.protein_change:
        variant_label = (
            variant.protein_change
        )

    elif (
        variant.reference_amino_acid
        and variant.protein_position
        is not None
        and variant.alternate_amino_acid
    ):
        variant_label = (
            f"{variant.reference_amino_acid}"
            f"{variant.protein_position}"
            f"{variant.alternate_amino_acid}"
        )

    else:
        variant_label = (
            "the analyzed variant"
        )

    impact_text = (
        prediction.impact_class
        if prediction.impact_class
        else "not assigned"
    )

    return (
        f"GeneMirror AI analyzed "
        f"{variant_label} in "
        f"{variant.gene_symbol}. "
        f"The current computational result "
        f"has an impact classification of "
        f"{impact_text}. "
        f"This classification is part of "
        f"GeneMirror's research-oriented "
        f"computational analysis and should "
        f"not be interpreted as a clinical "
        f"diagnosis."
    )


# ============================================================
# Prediction section
# ============================================================

def build_prediction_section(
    scientist_input: ScientistInput,
    evidence: List[GroundedEvidence],
) -> str:

    prediction_items = evidence_by_category(
        evidence,
        (
            "prediction",
            "calibration",
            "impact",
            "confidence",
            "uncertainty",
        ),
    )

    grounded_text = join_statements(
        prediction_items
    )

    return (
        f"{grounded_text} "
        f"{PREDICTION_INTERPRETATION} "
        f"{CONFIDENCE_INTERPRETATION}"
    )


# ============================================================
# Evidence / XAI section
# ============================================================

def build_evidence_section(
    evidence: List[GroundedEvidence],
) -> str:

    xai_items = evidence_by_category(
        evidence,
        ("xai",),
    )

    if not xai_items:

        return (
            "No local feature-contribution "
            "evidence was supplied for this "
            "analysis. "
            f"{XAI_INTERPRETATION}"
        )

    grounded_text = join_statements(
        xai_items
    )

    return (
        f"{grounded_text} "
        f"{XAI_INTERPRETATION}"
    )


# ============================================================
# Protein-context section
# ============================================================

def build_protein_context_section(
    evidence: List[GroundedEvidence],
) -> str:

    protein_items = evidence_by_category(
        evidence,
        (
            "protein",
            "protein_sequence",
            "protein_annotation",
        ),
    )

    if not protein_items:

        return (
            "No protein-context information "
            "was supplied for this analysis. "
            f"{PROTEIN_CONTEXT_INTERPRETATION}"
        )

    grounded_text = join_statements(
        protein_items
    )

    return (
        f"{grounded_text} "
        f"{PROTEIN_CONTEXT_INTERPRETATION}"
    )


# ============================================================
# Limitations section
# ============================================================

def build_limitations_section(
    scientist_input: ScientistInput,
) -> str:

    parts = [
        (
            "The prediction is based on a "
            "machine-learning model trained "
            "using a ClinVar-derived "
            "pathogenicity-proxy target."
        ),
        (
            "The model output does not directly "
            "measure molecular function and is "
            "not equivalent to clinical "
            "pathogenicity."
        ),
        (
            "Feature contributions describe "
            "model behavior rather than proving "
            "biological causation."
        ),
        (
            "Protein annotations provide "
            "context and do not independently "
            "establish functional disruption "
            "or disease relevance."
        ),
    ]

    prediction = scientist_input.prediction

    if (
        prediction.confidence_score
        is not None
    ):

        parts.append(
            (
                "The confidence score reflects "
                "model decisiveness and should "
                "not be interpreted as clinical "
                "certainty."
            )
        )

    if (
        prediction.confidence_band
        is not None
    ):

        parts.append(
            (
                "The confidence band is a "
                "presentation-level heuristic "
                "rather than a clinically "
                "validated confidence category."
            )
        )

    parts.append(
        (
            "The result is intended only for "
            "research and educational use."
        )
    )

    return " ".join(parts)


# ============================================================
# Complete deterministic summary
# ============================================================

def build_scientific_summary(
    scientist_input: ScientistInput,
) -> ScientistOutput:

    validate_scientist_input(
        scientist_input
    )

    evidence = build_grounded_evidence(
        scientist_input
    )

    verify_grounded_evidence(
        evidence
    )

    sections = (
        ScientistExplanationSections(
            overview=(
                build_overview_section(
                    scientist_input
                )
            ),
            prediction=(
                build_prediction_section(
                    scientist_input,
                    evidence,
                )
            ),
            evidence=(
                build_evidence_section(
                    evidence
                )
            ),
            protein_context=(
                build_protein_context_section(
                    evidence
                )
            ),
            limitations=(
                build_limitations_section(
                    scientist_input
                )
            ),
        )
    )

    output = ScientistOutput(
        variant=(
            scientist_input.variant.to_dict()
        ),
        sections=sections,
        grounded_facts=[
            item.to_dict()
            for item in evidence
        ],
        provider="deterministic",
        language_model=None,
        research_only=True,
    )

    validate_scientist_output(
        output
    )

    return output


# ============================================================
# Verification helper
# ============================================================

def verify_scientific_summary(
    output: ScientistOutput,
) -> None:

    validate_scientist_output(
        output
    )

    if not output.grounded_facts:

        raise ValueError(
            "Summary must preserve "
            "grounded facts."
        )

    if output.provider != "deterministic":

        raise ValueError(
            "Deterministic summary must "
            "identify its provider correctly."
        )

    if output.language_model is not None:

        raise ValueError(
            "Deterministic summary must not "
            "claim use of a language model."
        )


# ============================================================
# CLI smoke test
# ============================================================

def main():

    from backend.scientist.contracts import (
        ScientistFeatureContribution,
        ScientistInput,
        ScientistPrediction,
        ScientistProteinContext,
        ScientistVariant,
    )

    print(
        "GeneMirror Sprint 7 "
        "Grounded Scientific Summary Engine"
    )

    print("=" * 72)

    variant = ScientistVariant(
        gene_symbol="TP53",
        protein_change="R248H",
        protein_position=248,
        reference_amino_acid="R",
        alternate_amino_acid="H",
    )

    prediction = ScientistPrediction(
        predicted_class=0,
        predicted_class_name="benign_like",
        raw_model_score=0.3944095695,
        calibrated_probability=0.2228381375,
        impact_class="MODERATE",
        confidence_score=0.2346838982,
        uncertainty_score=0.7653161018,
        confidence_band="LOW",
        model_name=(
            "HistGradientBoostingClassifier"
        ),
        model_version=(
            "GeneMirror-v1-Sprint4"
        ),
    )

    contributions = [
        ScientistFeatureContribution(
            feature_name=(
                "abs_delta_molecular_weight"
            ),
            feature_value=18.02,
            contribution=0.065841,
            direction="supports_higher",
            relative_local_influence_percent=35.45,
        ),
        ScientistFeatureContribution(
            feature_name=(
                "delta_hydrophobicity"
            ),
            feature_value=-1.2,
            contribution=-0.028067,
            direction="supports_lower",
            relative_local_influence_percent=15.11,
        ),
    ]

    protein = ScientistProteinContext(
        accession="P04637",
        protein_name=(
            "Cellular tumor antigen p53"
        ),
        protein_length=393,
        sequence_window=(
            "CNSSCMGGMNRRPILTIITLE"
        ),
        window_start=238,
        window_end=258,
        overlapping_features=[
            {
                "feature_type": "Region",
                "start": 241,
                "end": 248,
                "description": (
                    "Interaction with the "
                    "53BP2 SH3 domain"
                ),
                "distance_to_variant": 0,
            }
        ],
        nearby_features=[
            {
                "feature_type": (
                    "Binding site"
                ),
                "start": 242,
                "end": 242,
                "description": None,
                "distance_to_variant": 6,
            }
        ],
    )

    scientist_input = ScientistInput(
        variant=variant,
        prediction=prediction,
        feature_contributions=contributions,
        protein_context=protein,
    )

    output = build_scientific_summary(
        scientist_input
    )

    verify_scientific_summary(
        output
    )

    print(
        "\nOVERVIEW"
    )
    print("-" * 72)
    print(
        output.sections.overview
    )

    print(
        "\nPREDICTION"
    )
    print("-" * 72)
    print(
        output.sections.prediction
    )

    print(
        "\nEVIDENCE"
    )
    print("-" * 72)
    print(
        output.sections.evidence
    )

    print(
        "\nPROTEIN CONTEXT"
    )
    print("-" * 72)
    print(
        output.sections.protein_context
    )

    print(
        "\nLIMITATIONS"
    )
    print("-" * 72)
    print(
        output.sections.limitations
    )

    print(
        "\nGrounded facts:",
        len(output.grounded_facts),
    )

    print(
        "Provider:",
        output.provider,
    )

    print(
        "Language model:",
        output.language_model,
    )

    print(
        "Research only:",
        output.research_only,
    )

    print(
        "\n✅ Grounded scientific "
        "summary completed."
    )


if __name__ == "__main__":
    main()