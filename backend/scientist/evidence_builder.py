import sys
from pathlib import Path
from typing import List


# ============================================================
# Make project root importable
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Imports
# ============================================================

from backend.scientist.contracts import (
    GroundedEvidence,
    ScientistInput,
    ScientistProteinContext,
    validate_scientist_input,
)


# ============================================================
# Formatting helpers
# ============================================================

def format_probability(value: float) -> str:
    return f"{value:.3f}"


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


# ============================================================
# Variant evidence
# ============================================================

def build_variant_evidence(
    scientist_input: ScientistInput,
) -> List[GroundedEvidence]:

    variant = scientist_input.variant
    evidence = []

    if variant.protein_change:

        evidence.append(
            GroundedEvidence(
                source="variant_input",
                category="variant",
                statement=(
                    f"The analyzed protein change is "
                    f"{variant.protein_change} in "
                    f"{variant.gene_symbol}."
                ),
                value=variant.protein_change,
            )
        )

    elif (
        variant.protein_position is not None
        and variant.reference_amino_acid
        and variant.alternate_amino_acid
    ):

        change = (
            f"{variant.reference_amino_acid}"
            f"{variant.protein_position}"
            f"{variant.alternate_amino_acid}"
        )

        evidence.append(
            GroundedEvidence(
                source="variant_input",
                category="variant",
                statement=(
                    f"The analyzed protein change is "
                    f"{change} in "
                    f"{variant.gene_symbol}."
                ),
                value=change,
            )
        )

    if (
        variant.chromosome
        and variant.position is not None
        and variant.reference_allele
        and variant.alternate_allele
    ):

        genomic_change = (
            f"{variant.chromosome}:"
            f"{variant.position} "
            f"{variant.reference_allele}>"
            f"{variant.alternate_allele}"
        )

        evidence.append(
            GroundedEvidence(
                source="variant_input",
                category="variant",
                statement=(
                    f"The genomic variant is "
                    f"{genomic_change}."
                ),
                value=genomic_change,
            )
        )

    return evidence


# ============================================================
# Prediction evidence
# ============================================================

def build_prediction_evidence(
    scientist_input: ScientistInput,
) -> List[GroundedEvidence]:

    prediction = scientist_input.prediction
    evidence = []

    raw_score_text = format_probability(
        prediction.raw_model_score
    )

    evidence.append(
        GroundedEvidence(
            source="variant_effect_model",
            category="prediction",
            statement=(
                f"The model produced a raw score of "
                f"{raw_score_text} for the "
                f"ClinVar-derived pathogenicity-proxy "
                f"target."
            ),
            value=prediction.raw_model_score,
            supports=prediction.predicted_class_name,
        )
    )

    evidence.append(
        GroundedEvidence(
            source="variant_effect_model",
            category="prediction",
            statement=(
                f"The model's predicted proxy class is "
                f"{prediction.predicted_class_name}."
            ),
            value=prediction.predicted_class_name,
        )
    )

    if prediction.calibrated_probability is not None:

        calibrated_text = format_probability(
            prediction.calibrated_probability
        )

        calibrated_percent = format_percent(
            prediction.calibrated_probability
        )

        evidence.append(
            GroundedEvidence(
                source="probability_calibration",
                category="calibration",
                statement=(
                    f"The calibrated probability for "
                    f"the pathogenic-like proxy class is "
                    f"{calibrated_text} "
                    f"({calibrated_percent})."
                ),
                value=(
                    prediction.calibrated_probability
                ),
                supports="pathogenic_like_proxy",
            )
        )

    if prediction.impact_class:

        evidence.append(
            GroundedEvidence(
                source="impact_mapper",
                category="impact",
                statement=(
                    f"The GeneMirror impact mapping "
                    f"classifies this result as "
                    f"{prediction.impact_class}."
                ),
                value=prediction.impact_class,
            )
        )

    if prediction.confidence_score is not None:

        confidence_value = (
            format_probability(
                prediction.confidence_score
            )
        )

        confidence_percent = (
            format_percent(
                prediction.confidence_score
            )
        )

        evidence.append(
            GroundedEvidence(
                source="confidence_engine",
                category="confidence",
                statement=(
                    f"The model decisiveness score is "
                    f"{confidence_value} "
                    f"({confidence_percent})."
                ),
                value=prediction.confidence_score,
            )
        )

    if prediction.confidence_band:

        evidence.append(
            GroundedEvidence(
                source="confidence_engine",
                category="confidence",
                statement=(
                    f"The presentation-level "
                    f"confidence band is "
                    f"{prediction.confidence_band}."
                ),
                value=prediction.confidence_band,
            )
        )

    if prediction.uncertainty_score is not None:

        uncertainty_value = (
            format_probability(
                prediction.uncertainty_score
            )
        )

        uncertainty_percent = (
            format_percent(
                prediction.uncertainty_score
            )
        )

        evidence.append(
            GroundedEvidence(
                source="confidence_engine",
                category="uncertainty",
                statement=(
                    f"The model uncertainty score is "
                    f"{uncertainty_value} "
                    f"({uncertainty_percent})."
                ),
                value=prediction.uncertainty_score,
            )
        )

    return evidence


# ============================================================
# XAI evidence
# ============================================================

def build_xai_evidence(
    scientist_input: ScientistInput,
    top_n: int = 5,
) -> List[GroundedEvidence]:

    if top_n <= 0:
        return []

    contributions = list(
        scientist_input.feature_contributions
    )

    contributions.sort(
        key=lambda item: abs(
            item.contribution
        ),
        reverse=True,
    )

    evidence = []

    for contribution in contributions[:top_n]:

        direction_text = {
            "supports_higher": (
                "toward a higher model score"
            ),
            "supports_lower": (
                "toward a lower model score"
            ),
            "neutral": (
                "with negligible directional effect"
            ),
        }[contribution.direction]

        statement = (
            f"The feature "
            f"{contribution.feature_name} "
            f"shifted the local prediction "
            f"{direction_text}."
        )

        influence = (
            contribution
            .relative_local_influence_percent
        )

        if influence is not None:

            statement += (
                f" Its relative local influence "
                f"was {influence:.2f}% of the "
                f"measured local perturbation "
                f"magnitude."
            )

        evidence.append(
            GroundedEvidence(
                source="local_xai",
                category="xai",
                statement=statement,
                value={
                    "feature_name": (
                        contribution.feature_name
                    ),
                    "feature_value": (
                        contribution.feature_value
                    ),
                    "contribution": (
                        contribution.contribution
                    ),
                    "relative_local_influence_percent": (
                        influence
                    ),
                },
                supports=contribution.direction,
            )
        )

    return evidence


# ============================================================
# Protein-context evidence
# ============================================================

def build_protein_evidence(
    protein_context: ScientistProteinContext,
    max_overlapping: int = 5,
    max_nearby: int = 5,
) -> List[GroundedEvidence]:

    evidence = []

    if protein_context.accession:

        evidence.append(
            GroundedEvidence(
                source="UniProtKB",
                category="protein",
                statement=(
                    f"The mapped UniProt accession is "
                    f"{protein_context.accession}."
                ),
                value=protein_context.accession,
            )
        )

    if protein_context.protein_name:

        evidence.append(
            GroundedEvidence(
                source="UniProtKB",
                category="protein",
                statement=(
                    f"The mapped protein is "
                    f"{protein_context.protein_name}."
                ),
                value=protein_context.protein_name,
            )
        )

    if (
        protein_context.sequence_window
        and protein_context.window_start is not None
        and protein_context.window_end is not None
    ):

        evidence.append(
            GroundedEvidence(
                source="UniProtKB",
                category="protein_sequence",
                statement=(
                    f"The local protein sequence window "
                    f"from residues "
                    f"{protein_context.window_start}-"
                    f"{protein_context.window_end} is "
                    f"{protein_context.sequence_window}."
                ),
                value=protein_context.sequence_window,
            )
        )

    for feature in (
        protein_context.overlapping_features[
            :max_overlapping
        ]
    ):

        feature_type = feature.get(
            "feature_type",
            "annotation",
        )

        start = feature.get("start")
        end = feature.get("end")

        description = feature.get(
            "description"
        )

        statement = (
            f"A UniProt {feature_type} "
            f"annotation overlaps the variant"
        )

        if (
            start is not None
            and end is not None
        ):

            statement += (
                f" at residues "
                f"{start}-{end}"
            )

        if description:
            statement += f": {description}"

        statement += "."

        evidence.append(
            GroundedEvidence(
                source="UniProtKB",
                category="protein_annotation",
                statement=statement,
                value=feature,
                supports="context_only",
            )
        )

    for feature in (
        protein_context.nearby_features[
            :max_nearby
        ]
    ):

        feature_type = feature.get(
            "feature_type",
            "annotation",
        )

        start = feature.get("start")
        end = feature.get("end")

        distance = feature.get(
            "distance_to_variant"
        )

        description = feature.get(
            "description"
        )

        statement = (
            f"A nearby UniProt "
            f"{feature_type} annotation"
        )

        if (
            start is not None
            and end is not None
        ):

            statement += (
                f" spans residues "
                f"{start}-{end}"
            )

        if distance is not None:

            statement += (
                f" and is {distance} residue"
            )

            if distance != 1:
                statement += "s"

            statement += (
                f" from the variant"
            )

        if description:
            statement += f": {description}"

        statement += "."

        evidence.append(
            GroundedEvidence(
                source="UniProtKB",
                category="protein_annotation",
                statement=statement,
                value=feature,
                supports="context_only",
            )
        )

    return evidence


# ============================================================
# Complete evidence builder
# ============================================================

def build_grounded_evidence(
    scientist_input: ScientistInput,
    top_xai_features: int = 5,
) -> List[GroundedEvidence]:

    validate_scientist_input(
        scientist_input
    )

    evidence = []

    evidence.extend(
        build_variant_evidence(
            scientist_input
        )
    )

    evidence.extend(
        build_prediction_evidence(
            scientist_input
        )
    )

    evidence.extend(
        build_xai_evidence(
            scientist_input,
            top_n=top_xai_features,
        )
    )

    if scientist_input.protein_context is not None:

        evidence.extend(
            build_protein_evidence(
                scientist_input.protein_context
            )
        )

    evidence.extend(
        scientist_input.grounded_evidence
    )

    return evidence


# ============================================================
# Verification helper
# ============================================================

def verify_grounded_evidence(
    evidence: List[GroundedEvidence],
) -> None:

    if not evidence:

        raise ValueError(
            "Grounded evidence cannot be empty."
        )

    for item in evidence:

        if not item.source.strip():

            raise ValueError(
                "Evidence source cannot be empty."
            )

        if not item.category.strip():

            raise ValueError(
                "Evidence category cannot be empty."
            )

        if not item.statement.strip():

            raise ValueError(
                "Evidence statement cannot be empty."
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
        "Structured Evidence Builder"
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

    evidence = build_grounded_evidence(
        scientist_input
    )

    verify_grounded_evidence(
        evidence
    )

    print(
        f"\nEvidence items: "
        f"{len(evidence)}"
    )

    print("\nGrounded evidence")
    print("-" * 72)

    for index, item in enumerate(
        evidence,
        start=1,
    ):

        print(
            f"{index:02}. "
            f"[{item.category}] "
            f"{item.statement}"
        )

    print(
        "\n✅ Structured evidence "
        "builder completed."
    )


if __name__ == "__main__":
    main()