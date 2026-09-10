from pathlib import Path


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXPLAINABILITY_DIR = (
    PROJECT_ROOT
    / "backend"
    / "explainability"
)

ARTIFACTS_DIR = (
    EXPLAINABILITY_DIR
    / "artifacts"
)

ARTIFACTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Frozen Sprint 4 model
# ============================================================

MODEL_ARTIFACT_PATH = (
    PROJECT_ROOT
    / "backend"
    / "modeling"
    / "artifacts"
    / "hist_gradient_boosting_v1.pkl"
)

MODEL_VERSION = "GeneMirror-v1-Sprint4"

MODEL_NAME = "HistGradientBoostingClassifier"


# ============================================================
# Sprint 5 versioning
# ============================================================

EXPLANATION_VERSION = "GeneMirror-XAI-v1"

CALIBRATION_VERSION = "GeneMirror-Calibration-v1"


# ============================================================
# Scientific terminology
# ============================================================

TARGET_INTERPRETATION = (
    "ClinVar-derived pathogenicity proxy for "
    "computational variant-effect modeling"
)

RAW_SCORE_INTERPRETATION = (
    "Uncalibrated model score produced by the frozen "
    "Sprint 4 classifier. It is not calibrated confidence "
    "and is not a clinical probability."
)

RESEARCH_DISCLAIMER = (
    "GeneMirror AI provides computational predictions "
    "for research and educational purposes only. "
    "Results are not clinical diagnoses and must not be "
    "used as medical advice."
)


# ============================================================
# User-facing impact classes
# ============================================================

IMPACT_CLASSES = (
    "LOW",
    "MODERATE",
    "HIGH",
)


# ============================================================
# Important:
# Thresholds are deliberately NOT defined here.
#
# They will be established only after probability calibration
# and uncertainty analysis later in Sprint 5.
# ============================================================