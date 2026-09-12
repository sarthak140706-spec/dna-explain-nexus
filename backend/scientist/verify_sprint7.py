import json
import sys
from pathlib import Path
from typing import Callable, List


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
    REQUIRED_EXPLANATION_SECTIONS,
    SCIENTIST_CONTRACT_VERSION,
    SCIENTIST_NAME,
    SCIENTIST_VERSION,
)

from backend.scientist.contracts import (
    ScientistFeatureContribution,
    ScientistInput,
    ScientistPrediction,
    ScientistProteinContext,
    ScientistVariant,
    validate_scientist_input,
    validate_scientist_output,
)

from backend.scientist.evidence_builder import (
    build_grounded_evidence,
    verify_grounded_evidence,
)

from backend.scientist.summary_engine import (
    build_scientific_summary,
    verify_scientific_summary,
)

from backend.scientist.prompt_builder import (
    build_prompt_package,
    verify_prompt_package,
)

from backend.scientist.llm_provider import (
    LLMProviderUnavailableError,
    create_llm_provider,
    verify_provider_response,
)

from backend.scientist.response_validator import (
    require_valid_provider_content,
    validate_provider_content,
)

from backend.scientist.scientist_engine import (
    run_gene_mirror_scientist,
    verify_scientist_result,
)


# ============================================================
# Verification tracker
# ============================================================

PASSED = 0
FAILED = 0
FAILURES: List[str] = []


def check(
    name: str,
    condition: bool,
) -> None:

    global PASSED
    global FAILED

    if condition:

        PASSED += 1
        print(
            f"  ✅ PASS: {name}"
        )

    else:

        FAILED += 1
        FAILURES.append(name)

        print(
            f"  ❌ FAIL: {name}"
        )


def check_raises(
    name: str,
    function: Callable,
) -> None:

    global PASSED
    global FAILED

    try:

        function()

    except Exception:

        PASSED += 1

        print(
            f"  ✅ PASS: {name}"
        )

        return

    FAILED += 1
    FAILURES.append(name)

    print(
        f"  ❌ FAIL: {name}"
    )


# ============================================================
# Reference Scientist input
# ============================================================

def build_reference_input() -> ScientistInput:

    variant = ScientistVariant(
        gene_symbol="TP53",
        chromosome="17",
        position=7674220,
        reference_allele="G",
        alternate_allele="A",
        dna_change="c.743G>A",
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

    protein_context = ScientistProteinContext(
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

    return ScientistInput(
        variant=variant,
        prediction=prediction,
        feature_contributions=(
            contributions
        ),
        protein_context=(
            protein_context
        ),
        source_versions={
            "model": (
                "GeneMirror-v1-Sprint4"
            ),
            "xai": (
                "GeneMirror-XAI-v1"
            ),
            "protein_context": (
                "GeneMirror-ProteinContext-v1"
            ),
        },
        research_only=True,
    )


# ============================================================
# Valid grounded provider payload
# ============================================================

def build_valid_provider_payload():

    return {
        "overview": (
            "GeneMirror AI analyzed R248H "
            "in TP53 and assigned a MODERATE "
            "computational impact classification."
        ),

        "prediction": (
            "The raw model score is 0.394. "
            "The predicted proxy class is "
            "benign_like. The calibrated "
            "probability for the pathogenic-like "
            "proxy class is 0.223 (22.3%). "
            "The impact classification is MODERATE. "
            "The model decisiveness score is "
            "0.235 (23.5%), with a LOW confidence "
            "band and uncertainty of 0.765 (76.5%)."
        ),

        "evidence": (
            "The feature "
            "abs_delta_molecular_weight had a "
            "relative local influence of 35.45%. "
            "The feature delta_hydrophobicity had "
            "a relative local influence of 15.11%. "
            "These values describe model behavior "
            "rather than biological causation."
        ),

        "protein_context": (
            "The mapped UniProt accession is "
            "P04637 for Cellular tumor antigen p53. "
            "The local sequence window spans "
            "238-258. Protein annotations provide "
            "context only."
        ),

        "limitations": (
            "This computational result is intended "
            "for research and educational use only. "
            "It is not a clinical conclusion or "
            "medical guidance."
        ),
    }


# ============================================================
# Main verification
# ============================================================

def main():

    global PASSED
    global FAILED

    print(
        "GeneMirror Sprint 7 "
        "Final Verification"
    )

    print("=" * 72)

    scientist_input = (
        build_reference_input()
    )

    # ========================================================
    # 1. Contracts
    # ========================================================

    print(
        "\n1. Scientist contracts"
    )

    print("-" * 72)

    validate_scientist_input(
        scientist_input
    )

    check(
        "Scientist name loaded",
        SCIENTIST_NAME
        == "GeneMirror Scientist",
    )

    check(
        "Scientist version loaded",
        bool(SCIENTIST_VERSION),
    )

    check(
        "Contract version loaded",
        bool(
            SCIENTIST_CONTRACT_VERSION
        ),
    )

    check(
        "Research-only input preserved",
        scientist_input.research_only
        is True,
    )

    check(
        "Gene preserved",
        scientist_input
        .variant
        .gene_symbol
        == "TP53",
    )

    check(
        "Protein change preserved",
        scientist_input
        .variant
        .protein_change
        == "R248H",
    )

    check(
        "Impact class preserved",
        scientist_input
        .prediction
        .impact_class
        == "MODERATE",
    )

    check(
        "Predicted proxy class preserved",
        scientist_input
        .prediction
        .predicted_class_name
        == "benign_like",
    )

    check(
        "Confidence and uncertainty distinct",
        scientist_input
        .prediction
        .confidence_score
        != scientist_input
        .prediction
        .uncertainty_score,
    )

    check(
        "Confidence + uncertainty equals 1",
        abs(
            scientist_input
            .prediction
            .confidence_score
            +
            scientist_input
            .prediction
            .uncertainty_score
            - 1.0
        )
        < 1e-9,
    )

    # ========================================================
    # 2. Structured evidence
    # ========================================================

    print(
        "\n2. Structured evidence builder"
    )

    print("-" * 72)

    evidence = build_grounded_evidence(
        scientist_input
    )

    verify_grounded_evidence(
        evidence
    )

    categories = [
        item.category
        for item in evidence
    ]

    sources = {
        item.source
        for item in evidence
    }

    statements = " ".join(
        item.statement
        for item in evidence
    )

    check(
        "Evidence generated",
        len(evidence) > 0,
    )

    check(
        "Variant evidence present",
        "variant" in categories,
    )

    check(
        "Prediction evidence present",
        "prediction" in categories,
    )

    check(
        "Calibration evidence present",
        "calibration" in categories,
    )

    check(
        "Impact evidence present",
        "impact" in categories,
    )

    check(
        "Confidence evidence present",
        "confidence" in categories,
    )

    check(
        "Uncertainty evidence present",
        "uncertainty" in categories,
    )

    check(
        "XAI evidence present",
        "xai" in categories,
    )

    check(
        "Protein evidence present",
        "protein" in categories,
    )

    check(
        "Protein annotation evidence present",
        "protein_annotation"
        in categories,
    )

    check(
        "Variant input source present",
        "variant_input" in sources,
    )

    check(
        "Model source present",
        "variant_effect_model"
        in sources,
    )

    check(
        "TP53 preserved in evidence",
        "TP53" in statements,
    )

    check(
        "R248H preserved in evidence",
        "R248H" in statements,
    )

    # ========================================================
    # 3. Deterministic scientific summary
    # ========================================================

    print(
        "\n3. Grounded scientific summary"
    )

    print("-" * 72)

    summary = build_scientific_summary(
        scientist_input
    )

    verify_scientific_summary(
        summary
    )

    validate_scientist_output(
        summary
    )

    sections_dict = (
        summary.sections.to_dict()
    )

    check(
        "All five sections present",
        set(
            sections_dict.keys()
        )
        == set(
            REQUIRED_EXPLANATION_SECTIONS
        ),
    )

    check(
        "Overview non-empty",
        bool(
            summary
            .sections
            .overview
            .strip()
        ),
    )

    check(
        "Prediction non-empty",
        bool(
            summary
            .sections
            .prediction
            .strip()
        ),
    )

    check(
        "Evidence section non-empty",
        bool(
            summary
            .sections
            .evidence
            .strip()
        ),
    )

    check(
        "Protein context non-empty",
        bool(
            summary
            .sections
            .protein_context
            .strip()
        ),
    )

    check(
        "Limitations non-empty",
        bool(
            summary
            .sections
            .limitations
            .strip()
        ),
    )

    check(
        "MODERATE preserved in overview",
        "MODERATE"
        in summary
        .sections
        .overview,
    )

    check(
        "benign_like preserved in prediction",
        "benign_like"
        in summary
        .sections
        .prediction,
    )

    check(
        "Clinical caution present",
        "clinical"
        in summary
        .sections
        .limitations
        .lower(),
    )

    check(
        "Research caution present",
        "research"
        in summary
        .sections
        .limitations
        .lower(),
    )

    check(
        "Deterministic provider identified",
        summary.provider
        == "deterministic",
    )

    check(
        "No language model claimed",
        summary.language_model
        is None,
    )

    check(
        "Grounded facts preserved",
        len(
            summary.grounded_facts
        )
        == len(evidence),
    )

    # ========================================================
    # 4. Prompt builder
    # ========================================================

    print(
        "\n4. Scientist prompt builder"
    )

    print("-" * 72)

    prompt_package = (
        build_prompt_package(
            scientist_input
        )
    )

    verify_prompt_package(
        prompt_package
    )

    combined_prompt = (
        prompt_package[
            "system_prompt"
        ]
        + "\n"
        + prompt_package[
            "user_prompt"
        ]
    )

    check(
        "Temperature fixed at zero",
        prompt_package[
            "temperature"
        ]
        == 0.0,
    )

    check(
        "JSON response requested",
        prompt_package[
            "response_format"
        ]
        == "json",
    )

    check(
        "Grounding data embedded",
        "GROUNDING DATA"
        in prompt_package[
            "user_prompt"
        ],
    )

    check(
        "Outside knowledge prohibited",
        "Do not use outside"
        in combined_prompt,
    )

    check(
        "Clinical inference prohibited",
        "Do not infer disease causation"
        in combined_prompt,
    )

    check(
        "XAI causality warning present",
        "Feature contributions describe model behavior"
        in combined_prompt,
    )

    check(
        "Protein-context warning present",
        "Protein annotations provide context only"
        in combined_prompt,
    )

    check(
        "Variant embedded in prompt",
        "R248H"
        in prompt_package[
            "user_prompt"
        ],
    )

    # ========================================================
    # 5. Provider interface
    # ========================================================

    print(
        "\n5. LLM provider interface"
    )

    print("-" * 72)

    mock_provider = (
        create_llm_provider(
            "mock"
        )
    )

    mock_response = (
        mock_provider.generate(
            system_prompt=(
                prompt_package[
                    "system_prompt"
                ]
            ),
            user_prompt=(
                prompt_package[
                    "user_prompt"
                ]
            ),
            temperature=0.0,
            response_format="json",
        )
    )

    verify_provider_response(
        mock_response
    )

    check(
        "Mock provider selected",
        mock_response.provider_name
        == "mock",
    )

    check(
        "Mock model identified",
        mock_response.model_name
        == "GeneMirror-Mock-LLM",
    )

    check(
        "Mock uses no external service",
        mock_response
        .used_external_service
        is False,
    )

    check(
        "Mock output is JSON",
        isinstance(
            json.loads(
                mock_response.content
            ),
            dict,
        ),
    )

    disabled_provider = (
        create_llm_provider(
            "disabled"
        )
    )

    def call_disabled():

        disabled_provider.generate(
            system_prompt=(
                prompt_package[
                    "system_prompt"
                ]
            ),
            user_prompt=(
                prompt_package[
                    "user_prompt"
                ]
            ),
            temperature=0.0,
            response_format="json",
        )

    check_raises(
        "Disabled provider refuses generation",
        call_disabled,
    )

    check_raises(
        "Unknown provider rejected",
        lambda: create_llm_provider(
            "definitely-not-real"
        ),
    )

    # ========================================================
    # 6. Response validator
    # ========================================================

    print(
        "\n6. Response validation "
        "and hallucination guards"
    )

    print("-" * 72)

    valid_payload = (
        build_valid_provider_payload()
    )

    valid_content = json.dumps(
        valid_payload
    )

    valid_report = (
        validate_provider_content(
            valid_content,
            scientist_input,
        )
    )

    check(
        "Valid grounded response accepted",
        valid_report.valid,
    )

    check(
        "Valid JSON check passed",
        "valid_json"
        in valid_report
        .checks_passed,
    )

    check(
        "Schema check passed",
        "valid_schema"
        in valid_report
        .checks_passed,
    )

    check(
        "Safety-language check passed",
        "safety_language"
        in valid_report
        .checks_passed,
    )

    check(
        "Semantic preservation passed",
        "semantic_preservation"
        in valid_report
        .checks_passed,
    )

    check(
        "Variant identity passed",
        "variant_identity"
        in valid_report
        .checks_passed,
    )

    check(
        "Numeric grounding passed",
        "numeric_grounding"
        in valid_report
        .checks_passed,
    )

    valid_sections = (
        require_valid_provider_content(
            valid_content,
            scientist_input,
        )
    )

    check(
        "Validated content converts "
        "to five sections",
        set(
            valid_sections
            .to_dict()
            .keys()
        )
        == set(
            REQUIRED_EXPLANATION_SECTIONS
        ),
    )

    # --------------------------------------------------------
    # Invalid JSON
    # --------------------------------------------------------

    invalid_json_report = (
        validate_provider_content(
            "not-json",
            scientist_input,
        )
    )

    check(
        "Invalid JSON rejected",
        not invalid_json_report.valid,
    )

    # --------------------------------------------------------
    # Missing section
    # --------------------------------------------------------

    missing_payload = dict(
        valid_payload
    )

    missing_payload.pop(
        "protein_context"
    )

    missing_report = (
        validate_provider_content(
            json.dumps(
                missing_payload
            ),
            scientist_input,
        )
    )

    check(
        "Missing section rejected",
        not missing_report.valid,
    )

    # --------------------------------------------------------
    # Extra section
    # --------------------------------------------------------

    extra_payload = dict(
        valid_payload
    )

    extra_payload[
        "diagnosis"
    ] = "unsupported"

    extra_report = (
        validate_provider_content(
            json.dumps(
                extra_payload
            ),
            scientist_input,
        )
    )

    check(
        "Extra section rejected",
        not extra_report.valid,
    )

    # --------------------------------------------------------
    # Clinical / causal hallucination
    # --------------------------------------------------------

    unsafe_payload = dict(
        valid_payload
    )

    unsafe_payload[
        "overview"
    ] = (
        "TP53 R248H causes cancer "
        "and is pathogenic."
    )

    unsafe_report = (
        validate_provider_content(
            json.dumps(
                unsafe_payload
            ),
            scientist_input,
        )
    )

    check(
        "Clinical/causal hallucination rejected",
        not unsafe_report.valid,
    )

    # --------------------------------------------------------
    # Wrong impact
    # --------------------------------------------------------

    wrong_impact_payload = dict(
        valid_payload
    )

    wrong_impact_payload[
        "overview"
    ] = (
        "GeneMirror AI analyzed "
        "R248H in TP53. "
        "The impact classification "
        "is HIGH."
    )

    wrong_impact_report = (
        validate_provider_content(
            json.dumps(
                wrong_impact_payload
            ),
            scientist_input,
        )
    )

    check(
        "Wrong impact class rejected",
        not wrong_impact_report.valid,
    )

    # --------------------------------------------------------
    # Invented number
    # --------------------------------------------------------

    numeric_payload = dict(
        valid_payload
    )

    numeric_payload[
        "prediction"
    ] += (
        " An additional probability "
        "is 99.9%."
    )

    numeric_report = (
        validate_provider_content(
            json.dumps(
                numeric_payload
            ),
            scientist_input,
        )
    )

    check(
        "Invented numerical value rejected",
        not numeric_report.valid,
    )

    # --------------------------------------------------------
    # Opposite proxy class
    # --------------------------------------------------------

    proxy_payload = dict(
        valid_payload
    )

    proxy_payload[
        "prediction"
    ] = (
        "The predicted proxy class "
        "is pathogenic_like. "
        "The raw model score is 0.394. "
        "The calibrated probability "
        "is 0.223 (22.3%). "
        "The impact classification "
        "is MODERATE."
    )

    proxy_report = (
        validate_provider_content(
            json.dumps(
                proxy_payload
            ),
            scientist_input,
        )
    )

    check(
        "Opposite proxy class rejected",
        not proxy_report.valid,
    )

    # ========================================================
    # 7. Integrated Scientist engine
    # ========================================================

    print(
        "\n7. Integrated Scientist engine"
    )

    print("-" * 72)

    disabled_result = (
        run_gene_mirror_scientist(
            scientist_input,
            provider_name="disabled",
        )
    )

    verify_scientist_result(
        disabled_result
    )

    check(
        "Disabled provider uses fallback",
        disabled_result[
            "metadata"
        ][
            "fallback_used"
        ]
        is True,
    )

    check(
        "Disabled fallback reason preserved",
        disabled_result[
            "metadata"
        ][
            "fallback_reason"
        ]
        == "provider_disabled",
    )

    check(
        "Disabled provider does not "
        "use LLM response",
        disabled_result[
            "metadata"
        ][
            "used_llm_response"
        ]
        is False,
    )

    check(
        "Fallback output remains research-only",
        disabled_result[
            "output"
        ]
        .research_only
        is True,
    )

    mock_result = (
        run_gene_mirror_scientist(
            scientist_input,
            provider_name="mock",
        )
    )

    verify_scientist_result(
        mock_result
    )

    check(
        "Ungrounded mock response "
        "triggers fallback",
        mock_result[
            "metadata"
        ][
            "fallback_used"
        ]
        is True,
    )

    check(
        "Mock rejection reason preserved",
        mock_result[
            "metadata"
        ][
            "fallback_reason"
        ]
        == "provider_response_rejected",
    )

    check(
        "Rejected mock response "
        "is not exposed",
        mock_result[
            "metadata"
        ][
            "used_llm_response"
        ]
        is False,
    )

    unknown_result = (
        run_gene_mirror_scientist(
            scientist_input,
            provider_name=(
                "definitely-not-real"
            ),
        )
    )

    verify_scientist_result(
        unknown_result
    )

    check(
        "Unknown provider triggers fallback",
        unknown_result[
            "metadata"
        ][
            "fallback_used"
        ]
        is True,
    )

    check(
        "Provider creation failure recorded",
        unknown_result[
            "metadata"
        ][
            "fallback_reason"
        ]
        == "provider_creation_failed",
    )

    # ========================================================
    # 8. Determinism
    # ========================================================

    print(
        "\n8. Determinism"
    )

    print("-" * 72)

    evidence_a = (
        build_grounded_evidence(
            scientist_input
        )
    )

    evidence_b = (
        build_grounded_evidence(
            scientist_input
        )
    )

    check(
        "Evidence builder deterministic",
        [
            item.to_dict()
            for item in evidence_a
        ]
        ==
        [
            item.to_dict()
            for item in evidence_b
        ],
    )

    summary_a = (
        build_scientific_summary(
            scientist_input
        )
    )

    summary_b = (
        build_scientific_summary(
            scientist_input
        )
    )

    check(
        "Summary deterministic",
        summary_a.to_dict()
        == summary_b.to_dict(),
    )

    prompt_a = (
        build_prompt_package(
            scientist_input
        )
    )

    prompt_b = (
        build_prompt_package(
            scientist_input
        )
    )

    check(
        "Prompt package deterministic",
        prompt_a == prompt_b,
    )

    engine_a = (
        run_gene_mirror_scientist(
            scientist_input,
            provider_name="disabled",
        )
    )

    engine_b = (
        run_gene_mirror_scientist(
            scientist_input,
            provider_name="disabled",
        )
    )

    check(
        "Integrated fallback output deterministic",
        engine_a[
            "output"
        ].to_dict()
        ==
        engine_b[
            "output"
        ].to_dict(),
    )

    check(
        "Execution metadata deterministic",
        engine_a[
            "metadata"
        ]
        ==
        engine_b[
            "metadata"
        ],
    )

    # ========================================================
    # 9. Semantic separation
    # ========================================================

    print(
        "\n9. Semantic separation"
    )

    print("-" * 72)

    prediction_text = (
        summary
        .sections
        .prediction
        .lower()
    )

    evidence_text = (
        summary
        .sections
        .evidence
        .lower()
    )

    protein_text = (
        summary
        .sections
        .protein_context
        .lower()
    )

    check(
        "Raw score identified separately",
        "raw score"
        in prediction_text,
    )

    check(
        "Calibrated probability identified",
        "calibrated probability"
        in prediction_text,
    )

    check(
        "Confidence described as decisiveness",
        "decisiveness"
        in prediction_text,
    )

    check(
        "Uncertainty independently present",
        "uncertainty"
        in prediction_text,
    )

    check(
        "XAI described as non-causal",
        (
            "do not establish "
            "biological causation"
            in evidence_text
        ),
    )

    check(
        "Protein overlap not treated "
        "as pathogenic proof",
        (
            "does not establish "
            "pathogenicity"
            in protein_text
        ),
    )

    check(
        "Impact and confidence remain distinct",
        (
            scientist_input
            .prediction
            .impact_class
            != scientist_input
            .prediction
            .confidence_band
        ),
    )

    # ========================================================
    # 10. Safety / final metadata
    # ========================================================

    print(
        "\n10. Safety and metadata"
    )

    print("-" * 72)

    final_output = (
        disabled_result[
            "output"
        ]
    )

    check(
        "Final output research-only",
        final_output.research_only
        is True,
    )

    check(
        "Final disclaimer present",
        bool(
            final_output
            .disclaimer
            .strip()
        ),
    )

    check(
        "No external LLM required",
        final_output.provider
        == "deterministic",
    )

    check(
        "No model falsely claimed",
        final_output.language_model
        is None,
    )

    check(
        "Scientist preserves "
        "grounded facts",
        len(
            final_output
            .grounded_facts
        )
        == len(evidence),
    )

    # ========================================================
    # Final result
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    print(
        "SPRINT 7 VERIFICATION SUMMARY"
    )

    print("=" * 72)

    print(
        f"Passed: {PASSED}"
    )

    print(
        f"Failed: {FAILED}"
    )

    if FAILURES:

        print(
            "\nFailed checks:"
        )

        for failure in FAILURES:

            print(
                f"  - {failure}"
            )

        raise SystemExit(
            "\n❌ SPRINT 7 VERIFICATION FAILED"
        )

    print(
        "\n✅ SPRINT 7 FINAL "
        "VERIFICATION PASSED"
    )


if __name__ == "__main__":
    main()