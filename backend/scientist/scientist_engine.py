import sys
from pathlib import Path
from typing import Any, Dict, Optional


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

from backend.scientist.contracts import (
    ScientistInput,
    ScientistOutput,
    validate_scientist_input,
    validate_scientist_output,
)

from backend.scientist.llm_provider import (
    LLMProviderError,
    LLMProviderUnavailableError,
    create_llm_provider,
)

from backend.scientist.prompt_builder import (
    build_prompt_package,
)

from backend.scientist.response_validator import (
    validate_provider_content,
    require_valid_provider_content,
)

from backend.scientist.summary_engine import (
    build_scientific_summary,
)


# ============================================================
# Scientist execution metadata
# ============================================================

def build_execution_metadata(
    *,
    requested_provider: Optional[str],
    provider_used: str,
    used_llm_response: bool,
    fallback_used: bool,
    fallback_reason: Optional[str],
    validation_errors: Optional[list] = None,
) -> Dict[str, Any]:

    return {
        "requested_provider": (
            requested_provider
        ),
        "provider_used": (
            provider_used
        ),
        "used_llm_response": (
            used_llm_response
        ),
        "fallback_used": (
            fallback_used
        ),
        "fallback_reason": (
            fallback_reason
        ),
        "validation_errors": (
            validation_errors or []
        ),
    }


# ============================================================
# Deterministic fallback
# ============================================================

def build_fallback_output(
    scientist_input: ScientistInput,
) -> ScientistOutput:

    output = build_scientific_summary(
        scientist_input
    )

    validate_scientist_output(
        output
    )

    return output


# ============================================================
# Main Scientist engine
# ============================================================

def run_gene_mirror_scientist(
    scientist_input: ScientistInput,
    provider_name: Optional[str] = None,
) -> Dict[str, Any]:

    validate_scientist_input(
        scientist_input
    )

    # --------------------------------------------------------
    # Always prepare the deterministic result first.
    # --------------------------------------------------------

    deterministic_output = (
        build_fallback_output(
            scientist_input
        )
    )

    # --------------------------------------------------------
    # Build prompt package.
    # --------------------------------------------------------

    prompt_package = (
        build_prompt_package(
            scientist_input
        )
    )

    # --------------------------------------------------------
    # Select provider.
    # --------------------------------------------------------

    try:

        provider = create_llm_provider(
            provider_name
        )

    except Exception as exc:

        metadata = build_execution_metadata(
            requested_provider=provider_name,
            provider_used="deterministic",
            used_llm_response=False,
            fallback_used=True,
            fallback_reason=(
                "provider_creation_failed"
            ),
            validation_errors=[
                str(exc)
            ],
        )

        return {
            "output": (
                deterministic_output
            ),
            "metadata": metadata,
        }

    # --------------------------------------------------------
    # Disabled provider means deterministic fallback.
    # --------------------------------------------------------

    if provider.provider_name == "disabled":

        metadata = build_execution_metadata(
            requested_provider=provider_name,
            provider_used="deterministic",
            used_llm_response=False,
            fallback_used=True,
            fallback_reason=(
                "provider_disabled"
            ),
        )

        return {
            "output": (
                deterministic_output
            ),
            "metadata": metadata,
        }

    # --------------------------------------------------------
    # Attempt provider generation.
    # --------------------------------------------------------

    try:

        provider_response = provider.generate(
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
            temperature=(
                prompt_package[
                    "temperature"
                ]
            ),
            response_format=(
                prompt_package[
                    "response_format"
                ]
            ),
        )

    except (
        LLMProviderUnavailableError,
        LLMProviderError,
        Exception,
    ) as exc:

        metadata = build_execution_metadata(
            requested_provider=provider_name,
            provider_used="deterministic",
            used_llm_response=False,
            fallback_used=True,
            fallback_reason=(
                "provider_generation_failed"
            ),
            validation_errors=[
                str(exc)
            ],
        )

        return {
            "output": (
                deterministic_output
            ),
            "metadata": metadata,
        }

    # --------------------------------------------------------
    # Validate provider output.
    # --------------------------------------------------------

    validation_report = (
        validate_provider_content(
            provider_response.content,
            scientist_input,
        )
    )

    if not validation_report.valid:

        metadata = build_execution_metadata(
            requested_provider=provider_name,
            provider_used="deterministic",
            used_llm_response=False,
            fallback_used=True,
            fallback_reason=(
                "provider_response_rejected"
            ),
            validation_errors=(
                validation_report.errors
            ),
        )

        return {
            "output": (
                deterministic_output
            ),
            "metadata": metadata,
        }

    # --------------------------------------------------------
    # Convert validated provider content into contract.
    # --------------------------------------------------------

    sections = (
        require_valid_provider_content(
            provider_response.content,
            scientist_input,
        )
    )

    llm_output = ScientistOutput(
        variant=(
            scientist_input
            .variant
            .to_dict()
        ),

        sections=sections,

        grounded_facts=(
            deterministic_output
            .grounded_facts
        ),

        provider=(
            provider_response
            .provider_name
        ),

        language_model=(
            provider_response
            .model_name
        ),

        research_only=True,
    )

    validate_scientist_output(
        llm_output
    )

    metadata = build_execution_metadata(
        requested_provider=provider_name,
        provider_used=(
            provider_response
            .provider_name
        ),
        used_llm_response=True,
        fallback_used=False,
        fallback_reason=None,
        validation_errors=[],
    )

    return {
        "output": llm_output,
        "metadata": metadata,
    }


# ============================================================
# Verification helper
# ============================================================

def verify_scientist_result(
    result: Dict[str, Any],
) -> None:

    if "output" not in result:
        raise ValueError(
            "Scientist result is missing output."
        )

    if "metadata" not in result:
        raise ValueError(
            "Scientist result is missing metadata."
        )

    output = result["output"]
    metadata = result["metadata"]

    if not isinstance(
        output,
        ScientistOutput,
    ):
        raise TypeError(
            "Scientist output must be "
            "ScientistOutput."
        )

    validate_scientist_output(
        output
    )

    required_metadata = {
        "requested_provider",
        "provider_used",
        "used_llm_response",
        "fallback_used",
        "fallback_reason",
        "validation_errors",
    }

    if not required_metadata.issubset(
        metadata.keys()
    ):
        raise ValueError(
            "Scientist execution metadata "
            "is incomplete."
        )

    if (
        metadata["used_llm_response"]
        and metadata["fallback_used"]
    ):
        raise ValueError(
            "LLM response and fallback cannot "
            "both be active."
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
        "Integrated Scientist Engine"
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
        feature_contributions=(
            contributions
        ),
        protein_context=protein,
    )

    # --------------------------------------------------------
    # Default provider test
    # --------------------------------------------------------

    print(
        "\nDefault provider test"
    )

    print("-" * 72)

    default_result = (
        run_gene_mirror_scientist(
            scientist_input
        )
    )

    verify_scientist_result(
        default_result
    )

    default_output = (
        default_result["output"]
    )

    default_metadata = (
        default_result["metadata"]
    )

    print(
        "Provider used:",
        default_metadata[
            "provider_used"
        ],
    )

    print(
        "Fallback used:",
        default_metadata[
            "fallback_used"
        ],
    )

    print(
        "Fallback reason:",
        default_metadata[
            "fallback_reason"
        ],
    )

    print(
        "Impact preserved:",
        "MODERATE"
        in default_output
        .sections
        .overview,
    )

    print(
        "Research only:",
        default_output.research_only,
    )

    # --------------------------------------------------------
    # Mock provider test
    # --------------------------------------------------------

    print(
        "\nMock provider test"
    )

    print("-" * 72)

    mock_result = (
        run_gene_mirror_scientist(
            scientist_input,
            provider_name="mock",
        )
    )

    verify_scientist_result(
        mock_result
    )

    mock_metadata = (
        mock_result["metadata"]
    )

    print(
        "Provider used:",
        mock_metadata[
            "provider_used"
        ],
    )

    print(
        "LLM response used:",
        mock_metadata[
            "used_llm_response"
        ],
    )

    print(
        "Fallback used:",
        mock_metadata[
            "fallback_used"
        ],
    )

    print(
        "Fallback reason:",
        mock_metadata[
            "fallback_reason"
        ],
    )

    print(
        "Validation errors:",
        mock_metadata[
            "validation_errors"
        ],
    )

    if not mock_metadata[
        "fallback_used"
    ]:

        raise ValueError(
            "Ungrounded mock response should "
            "have triggered fallback."
        )

    # --------------------------------------------------------
    # Unknown provider test
    # --------------------------------------------------------

    print(
        "\nUnknown provider test"
    )

    print("-" * 72)

    unknown_result = (
        run_gene_mirror_scientist(
            scientist_input,
            provider_name=(
                "not-a-real-provider"
            ),
        )
    )

    verify_scientist_result(
        unknown_result
    )

    unknown_metadata = (
        unknown_result["metadata"]
    )

    print(
        "Fallback used:",
        unknown_metadata[
            "fallback_used"
        ],
    )

    print(
        "Fallback reason:",
        unknown_metadata[
            "fallback_reason"
        ],
    )

    if not unknown_metadata[
        "fallback_used"
    ]:

        raise ValueError(
            "Unknown provider should "
            "trigger fallback."
        )

    print(
        "\n✅ Integrated GeneMirror "
        "Scientist engine completed."
    )


if __name__ == "__main__":
    main()