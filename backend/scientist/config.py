from pathlib import Path


# ============================================================
# Project paths
# ============================================================

CURRENT_FILE = Path(__file__).resolve()

SCIENTIST_DIR = CURRENT_FILE.parent

BACKEND_DIR = SCIENTIST_DIR.parent

PROJECT_ROOT = BACKEND_DIR.parent

ARTIFACTS_DIR = (
    SCIENTIST_DIR
    / "artifacts"
)


# ============================================================
# Version information
# ============================================================

SCIENTIST_VERSION = (
    "GeneMirror-Scientist-v1"
)

SCIENTIST_CONTRACT_VERSION = (
    "GeneMirror-Scientist-Contract-v1"
)


# ============================================================
# Scientist role
# ============================================================

SCIENTIST_NAME = (
    "GeneMirror Scientist"
)

SCIENTIST_ROLE = (
    "A grounded explanation layer that converts "
    "structured GeneMirror analysis results into "
    "clear research-oriented scientific summaries."
)


# ============================================================
# Grounding policy
# ============================================================

GROUNDING_POLICY = (
    "The GeneMirror Scientist must explain only "
    "information supplied by the GeneMirror backend. "
    "It must not invent biological evidence, variant "
    "effects, model scores, confidence values, protein "
    "annotations, clinical interpretations, diagnoses, "
    "or treatment recommendations."
)


# ============================================================
# Prediction interpretation
# ============================================================

PREDICTION_INTERPRETATION = (
    "The model score represents a computational estimate "
    "derived from a ClinVar-based pathogenicity proxy. "
    "It is not a clinical diagnosis or a direct probability "
    "that a variant causes disease."
)


# ============================================================
# Confidence interpretation
# ============================================================

CONFIDENCE_INTERPRETATION = (
    "The confidence score represents model decisiveness "
    "derived from the calibrated probability. "
    "It does not represent clinical certainty or complete "
    "biological certainty."
)


# ============================================================
# XAI interpretation
# ============================================================

XAI_INTERPRETATION = (
    "Feature contributions describe how individual model "
    "features influenced the computational prediction. "
    "They do not establish biological causation."
)


# ============================================================
# Protein context interpretation
# ============================================================

PROTEIN_CONTEXT_INTERPRETATION = (
    "Protein annotations provide contextual information "
    "about the variant location and nearby or overlapping "
    "UniProt annotations. Annotation overlap alone does "
    "not establish pathogenicity or functional disruption."
)


# ============================================================
# Safety
# ============================================================

RESEARCH_DISCLAIMER = (
    "GeneMirror AI provides computational predictions "
    "and explanations for research and educational "
    "purposes only. It is not intended for clinical "
    "diagnosis, treatment decisions, or medical advice."
)


# ============================================================
# Supported impact classes
# ============================================================

SUPPORTED_IMPACT_CLASSES = (
    "LOW",
    "MODERATE",
    "HIGH",
)


# ============================================================
# Output sections
# ============================================================

REQUIRED_EXPLANATION_SECTIONS = (
    "overview",
    "prediction",
    "evidence",
    "protein_context",
    "limitations",
)