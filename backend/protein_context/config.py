from pathlib import Path


# ============================================================
# Project paths
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

PROTEIN_CONTEXT_DIR = (
    PROJECT_ROOT
    / "backend"
    / "protein_context"
)

ARTIFACTS_DIR = (
    PROTEIN_CONTEXT_DIR
    / "artifacts"
)

ARTIFACTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Cache paths
# ============================================================

DATA_DIR = (
    PROJECT_ROOT
    / "data"
)

INTERIM_DATA_DIR = (
    DATA_DIR
    / "interim"
)

PROTEIN_CACHE_DIR = (
    INTERIM_DATA_DIR
    / "protein_context_cache"
)

PROTEIN_CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# UniProt configuration
# ============================================================

UNIPROT_BASE_URL = (
    "https://rest.uniprot.org"
)

UNIPROT_SEARCH_URL = (
    f"{UNIPROT_BASE_URL}"
    "/uniprotkb/search"
)

UNIPROT_ENTRY_URL = (
    f"{UNIPROT_BASE_URL}"
    "/uniprotkb"
)

HUMAN_TAXONOMY_ID = 9606

REQUEST_TIMEOUT_SECONDS = 30

MAX_RETRIES = 3

RETRY_BACKOFF_SECONDS = 1.0


# ============================================================
# Protein context configuration
# ============================================================

PROTEIN_CONTEXT_VERSION = (
    "GeneMirror-ProteinContext-v1"
)

PROTEIN_VISUALIZATION_VERSION = (
    "GeneMirror-ProteinVisualization-v1"
)

DEFAULT_SEQUENCE_WINDOW_RADIUS = 10

SUPPORTED_AMINO_ACIDS = set(
    "ACDEFGHIKLMNPQRSTVWY"
)


# ============================================================
# Feature categories
# ============================================================

SUPPORTED_FEATURE_TYPES = {
    "Domain",
    "Region",
    "Repeat",
    "Motif",
    "Active site",
    "Binding site",
    "Site",
    "Modified residue",
    "Disulfide bond",
    "Transmembrane",
    "Topological domain",
    "Signal peptide",
    "Peptide",
    "Chain",
}


# ============================================================
# Safety / interpretation
# ============================================================

PROTEIN_CONTEXT_INTERPRETATION = (
    "Protein context describes sequence and "
    "annotation information surrounding a variant. "
    "It does not independently establish pathogenicity "
    "or clinical significance."
)

RESEARCH_DISCLAIMER = (
    "GeneMirror AI provides computational predictions "
    "and protein-context information for research and "
    "educational purposes only. It is not intended for "
    "clinical diagnosis, treatment decisions, or other "
    "medical decision-making."
)