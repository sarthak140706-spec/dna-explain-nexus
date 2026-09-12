import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set


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
    REQUIRED_EXPLANATION_SECTIONS,
)

from backend.scientist.contracts import (
    ScientistExplanationSections,
    ScientistInput,
)

from backend.scientist.evidence_builder import (
    build_grounded_evidence,
)


# ============================================================
# Exceptions
# ============================================================

class ScientistResponseValidationError(
    ValueError
):
    """Base Scientist response validation error."""


class ScientistResponseJSONError(
    ScientistResponseValidationError
):
    """Raised when provider output is not valid JSON."""


class ScientistResponseSchemaError(
    ScientistResponseValidationError
):
    """Raised when output structure is invalid."""


class ScientistResponseSafetyError(
    ScientistResponseValidationError
):
    """Raised when unsafe claims are detected."""


class ScientistResponseGroundingError(
    ScientistResponseValidationError
):
    """Raised when grounding integrity fails."""


# ============================================================
# Validation report
# ============================================================

@dataclass
class ResponseValidationReport:
    valid: bool

    checks_passed: List[str] = field(
        default_factory=list
    )

    warnings: List[str] = field(
        default_factory=list
    )

    errors: List[str] = field(
        default_factory=list
    )

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "valid": self.valid,
            "checks_passed": (
                self.checks_passed
            ),
            "warnings": self.warnings,
            "errors": self.errors,
        }


# ============================================================
# High-risk language patterns
# ============================================================

FORBIDDEN_CLINICAL_PATTERNS = (
    # Direct diagnostic claims
    r"\bwe diagnose\b",
    r"\bthe diagnosis is\b",
    r"\bdiagnosed with\b",
    r"\bthis confirms a diagnosis\b",
    r"\bthe patient has\b",
    r"\bthe patient suffers from\b",

    # Direct treatment recommendations
    r"\brecommend(?:ed|ing)? treatment\b",
    r"\btreatment is recommended\b",
    r"\bshould be treated with\b",
    r"\btreat with\b",
    r"\btherapy is recommended\b",
    r"\bshould receive therapy\b",

    # Prescription / medication instructions
    r"\bwe prescribe\b",
    r"\bprescribe(?:d)?\s+[A-Za-z]",
    r"\bshould take\b",
    r"\bstart(?:ing)? medication\b",
    r"\bstop(?:ping)? medication\b",

    # Explicit medical recommendation language
    r"\bmedical recommendation\b",
    r"\bclinical recommendation\b",
    r"\btherapeutic recommendation\b",

    # Prognostic claims
    r"\bthe prognosis is\b",
    r"\bexpected survival\b",
)

FORBIDDEN_CAUSAL_PATTERNS = (
    r"\bcauses? disease\b",
    r"\bdisease[- ]causing\b",
    r"\bcauses? cancer\b",
    r"\bcauses? disorder\b",
    r"\bproves? pathogenicity\b",
    r"\bconfirms? pathogenicity\b",
    r"\bdefinitively pathogenic\b",
    r"\bdefinitively benign\b",
    r"\bis pathogenic\b",
    r"\bis benign\b",
)

FORBIDDEN_IMPACT_EQUIVALENCE_PATTERNS = (
    r"\bHIGH means pathogenic\b",
    r"\bHIGH means disease[- ]causing\b",
    r"\bLOW means benign\b",
    r"\bLOW means safe\b",
    r"\bMODERATE means pathogenic\b",
)

FORBIDDEN_XAI_PATTERNS = (
    r"\bfeature contribution proves\b",
    r"\bfeature contributions prove\b",
    r"\bXAI proves\b",
    r"\bcausal biological effect\b",
)

FORBIDDEN_PROTEIN_PATTERNS = (
    r"\bannotation proves\b",
    r"\bprotein annotation proves\b",
    r"\boverlap proves\b",
    r"\bprotein context proves\b",
)


# ============================================================
# Required caution concepts
# ============================================================

LIMITATION_CONCEPT_GROUPS = (
    (
        "research",
        "educational",
    ),
    (
        "clinical",
        "diagnosis",
        "medical",
    ),
)


# ============================================================
# JSON parsing
# ============================================================

def parse_provider_json(
    content: str,
) -> Dict[str, Any]:

    if not isinstance(content, str):

        raise ScientistResponseJSONError(
            "Provider response must be text."
        )

    if not content.strip():

        raise ScientistResponseJSONError(
            "Provider response cannot be empty."
        )

    try:

        parsed = json.loads(content)

    except json.JSONDecodeError as exc:

        raise ScientistResponseJSONError(
            "Provider response is not valid JSON."
        ) from exc

    if not isinstance(parsed, dict):

        raise ScientistResponseSchemaError(
            "Provider JSON must be an object."
        )

    return parsed


# ============================================================
# Schema validation
# ============================================================

def validate_response_schema(
    parsed: Dict[str, Any],
) -> None:

    expected_keys = set(
        REQUIRED_EXPLANATION_SECTIONS
    )

    actual_keys = set(
        parsed.keys()
    )

    missing = (
        expected_keys - actual_keys
    )

    extra = (
        actual_keys - expected_keys
    )

    if missing:

        raise ScientistResponseSchemaError(
            "Missing Scientist sections: "
            f"{sorted(missing)}"
        )

    if extra:

        raise ScientistResponseSchemaError(
            "Unexpected Scientist sections: "
            f"{sorted(extra)}"
        )

    for key in REQUIRED_EXPLANATION_SECTIONS:

        value = parsed[key]

        if not isinstance(value, str):

            raise ScientistResponseSchemaError(
                f"Section '{key}' must be text."
            )

        if not value.strip():

            raise ScientistResponseSchemaError(
                f"Section '{key}' cannot be empty."
            )


# ============================================================
# Text helpers
# ============================================================

def combine_sections(
    parsed: Dict[str, Any],
) -> str:

    return " ".join(
        parsed[key]
        for key in REQUIRED_EXPLANATION_SECTIONS
    )


def find_matching_patterns(
    text: str,
    patterns,
) -> List[str]:

    matches = []

    for pattern in patterns:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):

            matches.append(pattern)

    return matches


# ============================================================
# Safety validation
# ============================================================

def validate_safety_language(
    parsed: Dict[str, Any],
) -> None:

    text = combine_sections(
        parsed
    )

    pattern_groups = (
        (
            "clinical",
            FORBIDDEN_CLINICAL_PATTERNS,
        ),
        (
            "causal",
            FORBIDDEN_CAUSAL_PATTERNS,
        ),
        (
            "impact-equivalence",
            FORBIDDEN_IMPACT_EQUIVALENCE_PATTERNS,
        ),
        (
            "xai-causality",
            FORBIDDEN_XAI_PATTERNS,
        ),
        (
            "protein-causality",
            FORBIDDEN_PROTEIN_PATTERNS,
        ),
    )

    failures = []

    for group_name, patterns in pattern_groups:

        matches = find_matching_patterns(
            text,
            patterns,
        )

        if matches:

            failures.append(
                (
                    group_name,
                    matches,
                )
            )

    if failures:

        raise ScientistResponseSafetyError(
            "Unsafe or unsupported language "
            f"detected: {failures}"
        )


# ============================================================
# Limitation validation
# ============================================================

def validate_limitations(
    parsed: Dict[str, Any],
) -> None:

    limitations = (
        parsed["limitations"]
        .lower()
    )

    for concept_group in (
        LIMITATION_CONCEPT_GROUPS
    ):

        if not any(
            concept in limitations
            for concept in concept_group
        ):

            raise ScientistResponseSafetyError(
                "Limitations section is missing "
                "required research/clinical "
                "caution language."
            )


# ============================================================
# Semantic preservation
# ============================================================

def validate_semantic_preservation(
    parsed: Dict[str, Any],
    scientist_input: ScientistInput,
) -> None:

    text = combine_sections(
        parsed
    )

    prediction = (
        scientist_input.prediction
    )

    # Impact class must not silently change.
    if prediction.impact_class:

        impact = (
            prediction.impact_class
            .upper()
        )

        other_impacts = {
            "LOW",
            "MODERATE",
            "HIGH",
        } - {impact}

        text_upper = text.upper()

        if (
            impact not in text_upper
            and "impact" in text.lower()
        ):

            raise ScientistResponseGroundingError(
                "Response discusses impact but "
                "does not preserve the supplied "
                "impact class."
            )

        for other in other_impacts:

            pattern = (
                rf"\bimpact(?:\s+classification|\s+class)?"
                rf"[^.]*\b{other}\b"
            )

            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):

                raise ScientistResponseGroundingError(
                    "Response appears to introduce "
                    "an impact class different from "
                    "the supplied result."
                )

    # Proxy class should not be replaced by the
    # opposite class when explicitly discussed.
    supplied_class = (
        prediction.predicted_class_name
    )

    opposite_class = {
        "benign_like": "pathogenic_like",
        "pathogenic_like": "benign_like",
    }.get(supplied_class)

    if opposite_class:

        prediction_section = (
            parsed["prediction"]
            .lower()
        )

        if (
            "predicted proxy class"
            in prediction_section
            and opposite_class
            in prediction_section
        ):

            raise ScientistResponseGroundingError(
                "Response changes the supplied "
                "predicted proxy class."
            )


# ============================================================
# Variant identity grounding
# ============================================================

def validate_variant_identity(
    parsed: Dict[str, Any],
    scientist_input: ScientistInput,
) -> None:

    text = combine_sections(
        parsed
    )

    variant = scientist_input.variant

    gene = variant.gene_symbol

    if gene and gene.upper() not in text.upper():

        raise ScientistResponseGroundingError(
            "Scientist response does not preserve "
            "the supplied gene symbol."
        )

    if variant.protein_change:

        if (
            variant.protein_change.upper()
            not in text.upper()
        ):

            raise ScientistResponseGroundingError(
                "Scientist response does not preserve "
                "the supplied protein change."
            )


# ============================================================
# Numerical grounding
# ============================================================

NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z])"
    r"-?\d+(?:\.\d+)?"
    r"(?:%)?"
)


def extract_numbers(
    text: str,
) -> Set[str]:

    return set(
        NUMBER_PATTERN.findall(
            text
        )
    )


def build_allowed_numeric_tokens(
    scientist_input: ScientistInput,
) -> Set[str]:

    evidence = build_grounded_evidence(
        scientist_input
    )

    allowed = set()

    for item in evidence:

        allowed.update(
            extract_numbers(
                item.statement
            )
        )

    # Allow harmless common textual values that
    # may appear in safety wording or formatting.
    allowed.update(
        {
            "0",
            "1",
            "0.0",
            "1.0",
            "0%",
            "100%",
        }
    )

    return allowed


def validate_numeric_grounding(
    parsed: Dict[str, Any],
    scientist_input: ScientistInput,
) -> None:

    response_numbers = (
        extract_numbers(
            combine_sections(
                parsed
            )
        )
    )

    allowed_numbers = (
        build_allowed_numeric_tokens(
            scientist_input
        )
    )

    unsupported = (
        response_numbers
        - allowed_numbers
    )

    if unsupported:

        raise ScientistResponseGroundingError(
            "Response contains numerical values "
            "not present in grounded evidence: "
            f"{sorted(unsupported)}"
        )


# ============================================================
# Build explanation contract
# ============================================================

def build_explanation_sections(
    parsed: Dict[str, Any],
) -> ScientistExplanationSections:

    return ScientistExplanationSections(
        overview=parsed["overview"].strip(),
        prediction=parsed["prediction"].strip(),
        evidence=parsed["evidence"].strip(),
        protein_context=(
            parsed["protein_context"].strip()
        ),
        limitations=(
            parsed["limitations"].strip()
        ),
    )


# ============================================================
# Complete validation
# ============================================================

def validate_provider_content(
    content: str,
    scientist_input: ScientistInput,
) -> ResponseValidationReport:

    report = ResponseValidationReport(
        valid=False
    )

    try:

        parsed = parse_provider_json(
            content
        )

        report.checks_passed.append(
            "valid_json"
        )

        validate_response_schema(
            parsed
        )

        report.checks_passed.append(
            "valid_schema"
        )

        validate_safety_language(
            parsed
        )

        report.checks_passed.append(
            "safety_language"
        )

        validate_limitations(
            parsed
        )

        report.checks_passed.append(
            "limitations_present"
        )

        validate_semantic_preservation(
            parsed,
            scientist_input,
        )

        report.checks_passed.append(
            "semantic_preservation"
        )

        validate_variant_identity(
            parsed,
            scientist_input,
        )

        report.checks_passed.append(
            "variant_identity"
        )

        validate_numeric_grounding(
            parsed,
            scientist_input,
        )

        report.checks_passed.append(
            "numeric_grounding"
        )

    except ScientistResponseValidationError as exc:

        report.errors.append(
            str(exc)
        )

        return report

    report.valid = True

    return report


# ============================================================
# Strict validation helper
# ============================================================

def require_valid_provider_content(
    content: str,
    scientist_input: ScientistInput,
) -> ScientistExplanationSections:

    report = validate_provider_content(
        content,
        scientist_input,
    )

    if not report.valid:

        raise ScientistResponseValidationError(
            "; ".join(
                report.errors
            )
        )

    parsed = parse_provider_json(
        content
    )

    return build_explanation_sections(
        parsed
    )


# ============================================================
# CLI verification
# ============================================================

def main():

    from backend.scientist.contracts import (
        ScientistInput,
        ScientistPrediction,
        ScientistVariant,
    )

    print(
        "GeneMirror Sprint 7 "
        "Response Validation & "
        "Hallucination Guards"
    )

    print("=" * 72)

    variant = ScientistVariant(
        gene_symbol="TP53",
        protein_change="R248H",
    )

    prediction = ScientistPrediction(
        predicted_class=0,
        predicted_class_name="benign_like",
        raw_model_score=0.3944,
        calibrated_probability=0.2228,
        impact_class="MODERATE",
        confidence_score=0.2347,
        uncertainty_score=0.7653,
        confidence_band="LOW",
    )

    scientist_input = ScientistInput(
        variant=variant,
        prediction=prediction,
    )

    # --------------------------------------------------------
    # Valid response
    # --------------------------------------------------------

    valid_payload = {
        "overview": (
            "GeneMirror AI analyzed R248H in TP53 "
            "and assigned a MODERATE computational "
            "impact classification."
        ),

        "prediction": (
            "The model produced a raw score of 0.394 "
            "for the ClinVar-derived proxy target. "
            "The predicted proxy class is benign_like. "
            "The calibrated probability for the "
            "pathogenic-like proxy class is 0.223 "
            "(22.3%). The impact classification is "
            "MODERATE. The model decisiveness score "
            "is 0.235 (23.5%) and the confidence band "
            "is LOW. The uncertainty score is 0.765 "
            "(76.5%)."
        ),

        "evidence": (
            "No local feature-contribution evidence "
            "was supplied for this analysis."
        ),

        "protein_context": (
            "No protein-context information was "
            "supplied for this analysis."
        ),

        "limitations": (
            "This computational result is intended "
            "for research and educational use only. "
            "It should not be treated as clinical "
            "certainty or medical guidance."
        ),
    }

    valid_content = json.dumps(
        valid_payload
    )

    valid_report = (
        validate_provider_content(
            valid_content,
            scientist_input,
        )
    )

    print(
        "\nValid grounded response"
    )

    print("-" * 72)

    print(
        "Valid:",
        valid_report.valid,
    )

    print(
        "Checks:",
        valid_report.checks_passed,
    )

    if not valid_report.valid:

        raise ValueError(
            valid_report.errors
        )

    # --------------------------------------------------------
    # Invalid JSON
    # --------------------------------------------------------

    print(
        "\nInvalid JSON test"
    )

    print("-" * 72)

    invalid_json_report = (
        validate_provider_content(
            "not-json",
            scientist_input,
        )
    )

    print(
        "Rejected:",
        not invalid_json_report.valid,
    )

    # --------------------------------------------------------
    # Extra section
    # --------------------------------------------------------

    extra_payload = dict(
        valid_payload
    )

    extra_payload["diagnosis"] = (
        "unsupported"
    )

    extra_report = (
        validate_provider_content(
            json.dumps(
                extra_payload
            ),
            scientist_input,
        )
    )

    print(
        "Extra section rejected:",
        not extra_report.valid,
    )

    # --------------------------------------------------------
    # Clinical/causal hallucination
    # --------------------------------------------------------

    unsafe_payload = dict(
        valid_payload
    )

    unsafe_payload["overview"] = (
        "TP53 R248H causes cancer and "
        "is pathogenic."
    )

    unsafe_report = (
        validate_provider_content(
            json.dumps(
                unsafe_payload
            ),
            scientist_input,
        )
    )

    print(
        "Clinical/causal claim rejected:",
        not unsafe_report.valid,
    )

    # --------------------------------------------------------
    # Invented number
    # --------------------------------------------------------

    numeric_payload = dict(
        valid_payload
    )

    numeric_payload["prediction"] += (
        " The probability is 99.9%."
    )

    numeric_report = (
        validate_provider_content(
            json.dumps(
                numeric_payload
            ),
            scientist_input,
        )
    )

    print(
        "Invented number rejected:",
        not numeric_report.valid,
    )

    # --------------------------------------------------------
    # Wrong impact
    # --------------------------------------------------------

    impact_payload = dict(
        valid_payload
    )

    impact_payload["overview"] = (
        "GeneMirror AI analyzed R248H in TP53. "
        "The impact classification is HIGH."
    )

    impact_report = (
        validate_provider_content(
            json.dumps(
                impact_payload
            ),
            scientist_input,
        )
    )

    print(
        "Wrong impact rejected:",
        not impact_report.valid,
    )

    all_checks = (
        valid_report.valid
        and not invalid_json_report.valid
        and not extra_report.valid
        and not unsafe_report.valid
        and not numeric_report.valid
        and not impact_report.valid
    )

    if not all_checks:

        raise ValueError(
            "One or more Scientist response "
            "validation tests failed."
        )

    print(
        "\n✅ Response validation and "
        "hallucination guards completed."
    )


if __name__ == "__main__":
    main()