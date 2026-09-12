import json
import sys
from pathlib import Path
from typing import Any, Dict, List


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

from backend.scientist.config import (
    GROUNDING_POLICY,
    RESEARCH_DISCLAIMER,
    REQUIRED_EXPLANATION_SECTIONS,
    SCIENTIST_NAME,
    SCIENTIST_ROLE,
)

from backend.scientist.contracts import (
    GroundedEvidence,
    ScientistInput,
    validate_scientist_input,
)

from backend.scientist.evidence_builder import (
    build_grounded_evidence,
    verify_grounded_evidence,
)

from backend.scientist.summary_engine import (
    build_scientific_summary,
)


# ============================================================
# System prompt
# ============================================================

def build_system_prompt() -> str:

    required_sections = ", ".join(
        REQUIRED_EXPLANATION_SECTIONS
    )

    return (
        f"You are {SCIENTIST_NAME}. "
        f"{SCIENTIST_ROLE}\n\n"

        "GROUNDING RULES:\n"
        f"1. {GROUNDING_POLICY}\n"
        "2. Use only the facts supplied in the "
        "GROUNDING DATA section.\n"
        "3. Do not use outside biological or clinical "
        "knowledge to add new claims.\n"
        "4. Do not infer disease causation, diagnosis, "
        "treatment, prognosis, or medical advice.\n"
        "5. Do not reinterpret LOW, MODERATE, or HIGH "
        "as benign, pathogenic, safe, or disease-causing.\n"
        "6. Keep raw model score, calibrated probability, "
        "impact class, confidence, and uncertainty as "
        "separate concepts.\n"
        "7. Feature contributions describe model behavior "
        "and must not be described as causal biology.\n"
        "8. Protein annotations provide context only and "
        "must not be presented as proof of pathogenicity.\n"
        "9. If a requested fact is not supplied, state "
        "that it is not available from the current analysis.\n"
        "10. Preserve numerical values faithfully. Do not "
        "change or estimate them.\n\n"

        "OUTPUT RULES:\n"
        "Return valid JSON only.\n"
        f"Use exactly these section names: "
        f"{required_sections}.\n"
        "Each section value must be a non-empty string.\n"
        "Do not add markdown formatting.\n"
        "Do not add extra top-level keys.\n"
        f"Preserve this safety meaning: "
        f"{RESEARCH_DISCLAIMER}"
    )


# ============================================================
# Grounding payload
# ============================================================

def build_grounding_payload(
    scientist_input: ScientistInput,
) -> Dict[str, Any]:

    validate_scientist_input(
        scientist_input
    )

    evidence = build_grounded_evidence(
        scientist_input
    )

    verify_grounded_evidence(
        evidence
    )

    deterministic_summary = (
        build_scientific_summary(
            scientist_input
        )
    )

    return {
        "variant": (
            scientist_input.variant.to_dict()
        ),

        "prediction": (
            scientist_input.prediction.to_dict()
        ),

        "grounded_evidence": [
            item.to_dict()
            for item in evidence
        ],

        "deterministic_summary": (
            deterministic_summary
            .sections
            .to_dict()
        ),

        "research_only": True,

        "disclaimer": (
            RESEARCH_DISCLAIMER
        ),
    }


# ============================================================
# User prompt
# ============================================================

def build_user_prompt(
    scientist_input: ScientistInput,
) -> str:

    payload = build_grounding_payload(
        scientist_input
    )

    payload_json = json.dumps(
        payload,
        indent=2,
        ensure_ascii=False,
    )

    return (
        "Rewrite the deterministic GeneMirror analysis "
        "into a clearer, concise scientific explanation "
        "while preserving the supplied facts exactly.\n\n"

        "Do not add new scientific claims.\n"
        "Do not use outside knowledge.\n"
        "Do not convert computational results into "
        "clinical conclusions.\n\n"

        "GROUNDING DATA:\n"
        f"{payload_json}\n\n"

        "Return JSON with exactly this structure:\n"
        "{\n"
        '  "overview": "...",\n'
        '  "prediction": "...",\n'
        '  "evidence": "...",\n'
        '  "protein_context": "...",\n'
        '  "limitations": "..."\n'
        "}"
    )


# ============================================================
# Complete prompt package
# ============================================================

def build_prompt_package(
    scientist_input: ScientistInput,
) -> Dict[str, Any]:

    system_prompt = build_system_prompt()

    user_prompt = build_user_prompt(
        scientist_input
    )

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "temperature": 0.0,
        "response_format": "json",
    }


# ============================================================
# Verification
# ============================================================

def verify_prompt_package(
    prompt_package: Dict[str, Any],
) -> None:

    required_keys = {
        "system_prompt",
        "user_prompt",
        "temperature",
        "response_format",
    }

    if not required_keys.issubset(
        prompt_package.keys()
    ):
        raise ValueError(
            "Prompt package is missing required keys."
        )

    system_prompt = prompt_package[
        "system_prompt"
    ]

    user_prompt = prompt_package[
        "user_prompt"
    ]

    if not system_prompt.strip():
        raise ValueError(
            "System prompt cannot be empty."
        )

    if not user_prompt.strip():
        raise ValueError(
            "User prompt cannot be empty."
        )

    if prompt_package[
        "temperature"
    ] != 0.0:
        raise ValueError(
            "Scientist temperature must remain 0.0."
        )

    if prompt_package[
        "response_format"
    ] != "json":
        raise ValueError(
            "Scientist response format must be JSON."
        )

    required_phrases = [
        "Do not use outside biological or clinical knowledge",
        "Feature contributions describe model behavior",
        "Protein annotations provide context only",
        "Return valid JSON only",
        "GROUNDING DATA",
    ]

    combined = (
        system_prompt
        + "\n"
        + user_prompt
    )

    for phrase in required_phrases:

        if phrase not in combined:

            raise ValueError(
                f"Required grounding phrase missing: "
                f"{phrase}"
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
        "Scientist Prompt Builder"
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
        model_name="HistGradientBoostingClassifier",
        model_version="GeneMirror-v1-Sprint4",
    )

    contributions = [
        ScientistFeatureContribution(
            feature_name="abs_delta_molecular_weight",
            feature_value=18.02,
            contribution=0.065841,
            direction="supports_higher",
            relative_local_influence_percent=35.45,
        ),
        ScientistFeatureContribution(
            feature_name="delta_hydrophobicity",
            feature_value=-1.2,
            contribution=-0.028067,
            direction="supports_lower",
            relative_local_influence_percent=15.11,
        ),
    ]

    protein = ScientistProteinContext(
        accession="P04637",
        protein_name="Cellular tumor antigen p53",
        protein_length=393,
        sequence_window="CNSSCMGGMNRRPILTIITLE",
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
                "feature_type": "Binding site",
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

    package = build_prompt_package(
        scientist_input
    )

    verify_prompt_package(
        package
    )

    print(
        "\nSystem prompt length:",
        len(
            package[
                "system_prompt"
            ]
        ),
    )

    print(
        "User prompt length:",
        len(
            package[
                "user_prompt"
            ]
        ),
    )

    print(
        "Temperature:",
        package[
            "temperature"
        ],
    )

    print(
        "Response format:",
        package[
            "response_format"
        ],
    )

    print(
        "\nGrounding checks"
    )

    print("-" * 72)

    checks = {
        "No outside knowledge": (
            "Do not use outside biological "
            "or clinical knowledge"
            in package["system_prompt"]
        ),

        "No clinical inference": (
            "Do not infer disease causation"
            in package["system_prompt"]
        ),

        "Semantic separation": (
            "Keep raw model score"
            in package["system_prompt"]
        ),

        "XAI caution": (
            "Feature contributions describe "
            "model behavior"
            in package["system_prompt"]
        ),

        "Protein caution": (
            "Protein annotations provide "
            "context only"
            in package["system_prompt"]
        ),

        "Grounding data embedded": (
            "GROUNDING DATA"
            in package["user_prompt"]
        ),

        "Variant embedded": (
            "R248H"
            in package["user_prompt"]
        ),

        "Impact embedded": (
            "MODERATE"
            in package["user_prompt"]
        ),

        "Confidence embedded": (
            "LOW"
            in package["user_prompt"]
        ),
    }

    for name, passed in checks.items():

        print(
            f"{name}: {passed}"
        )

    if not all(
        checks.values()
    ):
        raise ValueError(
            "One or more prompt grounding "
            "checks failed."
        )

    print(
        "\n✅ Scientist prompt builder "
        "verification completed."
    )


if __name__ == "__main__":
    main()