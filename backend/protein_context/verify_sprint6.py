import sys
from pathlib import Path


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.protein_context.config import (
    HUMAN_TAXONOMY_ID,
    PROTEIN_CONTEXT_VERSION,
    PROTEIN_VISUALIZATION_VERSION,
)

from backend.protein_context.context_engine import (
    build_sequence_context,
    get_local_protein_context,
    verify_local_context,
)

from backend.protein_context.contracts import (
    ProteinContextResult,
    validate_protein_context_contract,
)

from backend.protein_context.feature_context import (
    calculate_feature_distance,
    get_variant_feature_context,
    verify_feature_context,
)

from backend.protein_context.parser import (
    parse_uniprot_entry,
    verify_parsed_protein,
)

from backend.protein_context.uniprot_client import (
    get_reviewed_human_protein,
)

from backend.protein_context.variant_validator import (
    ProteinPositionOutOfRangeError,
    ReferenceAminoAcidMismatchError,
    validate_variant_for_gene,
)

from backend.protein_context.visualization_engine import (
    build_protein_visualization,
    normalize_position,
    verify_visualization_payload,
)


passed = 0
failed = 0


def check(condition, name):

    global passed, failed

    if condition:
        print(f"[PASS] {name}")
        passed += 1
    else:
        print(f"[FAIL] {name}")
        failed += 1


print("=" * 80)
print("GeneMirror Sprint 6 Final Verification")
print("=" * 80)


# ============================================================
# 1. UniProt retrieval
# ============================================================

print("\n1. UniProt retrieval")

result = get_reviewed_human_protein("TP53")

entry = result["entry"]

check(
    result["accession"] == "P04637",
    "TP53 reviewed UniProt accession resolved",
)

check(
    entry.get("organism", {}).get("taxonId")
    == HUMAN_TAXONOMY_ID,
    "Human taxonomy ID is 9606",
)

check(
    bool(entry.get("sequence", {}).get("value")),
    "Protein sequence present",
)


# ============================================================
# 2. Protein parsing
# ============================================================

print("\n2. Protein parsing")

parsed = parse_uniprot_entry(entry)

verify_parsed_protein(parsed)

identity = parsed["identity"]

check(
    identity.gene_symbol == "TP53",
    "Gene symbol parsed",
)

check(
    identity.reviewed is True,
    "Reviewed status parsed",
)

check(
    identity.sequence_length
    == len(parsed["sequence"]),
    "Sequence length matches",
)

check(
    parsed["feature_count"] > 0,
    "Protein features parsed",
)


# ============================================================
# 3. Variant validation
# ============================================================

print("\n3. Variant validation")

validation = validate_variant_for_gene(
    "TP53",
    248,
    "R",
    "H",
)

check(
    validation["position_matches_reference"] is True,
    "TP53 R248 reference residue validated",
)

check(
    validation["amino_acid_change"] == "R248H",
    "Amino-acid change generated",
)

try:
    validate_variant_for_gene(
        "TP53",
        248,
        "A",
        "H",
    )
    mismatch_rejected = False
except ReferenceAminoAcidMismatchError:
    mismatch_rejected = True

check(
    mismatch_rejected,
    "Wrong reference amino acid rejected",
)

try:
    validate_variant_for_gene(
        "TP53",
        999,
        "R",
        "H",
    )
    out_of_range_rejected = False
except ProteinPositionOutOfRangeError:
    out_of_range_rejected = True

check(
    out_of_range_rejected,
    "Out-of-range protein position rejected",
)


# ============================================================
# 4. Local sequence context
# ============================================================

print("\n4. Local sequence context")

local = get_local_protein_context(
    "TP53",
    248,
    "R",
    "H",
)

verify_local_context(local)

ctx = local["sequence_context"]

check(
    ctx.window_start == 238,
    "Window start correct",
)

check(
    ctx.window_end == 258,
    "Window end correct",
)

check(
    len(ctx.sequence_window) == 21,
    "Window length is 21",
)

check(
    ctx.sequence_window[
        ctx.variant_index_in_window
    ] == "R",
    "Variant residue present inside window",
)


# ============================================================
# 5. Boundary behavior
# ============================================================

print("\n5. Sequence boundary behavior")

test_sequence = "ACDEFGHIKLMNPQRSTVWY"

start_context = build_sequence_context(
    test_sequence,
    1,
    "A",
    "C",
    10,
)

end_context = build_sequence_context(
    test_sequence,
    20,
    "Y",
    "A",
    10,
)

check(
    (
        start_context.window_start == 1
        and start_context.variant_index_in_window == 0
    ),
    "N-terminal window clipped correctly",
)

check(
    (
        end_context.window_end == 20
        and end_context.variant_index_in_window == 10
    ),
    "C-terminal window clipped correctly",
)


# ============================================================
# 6. Feature context
# ============================================================

print("\n6. Protein feature context")

feature_result = get_variant_feature_context(
    "TP53",
    248,
    "R",
    "H",
    nearby_radius=15,
)

verify_feature_context(feature_result)

check(
    len(
        feature_result["overlapping_features"]
    ) > 0,
    "Overlapping protein annotations found",
)

check(
    all(
        f.distance_to_variant == 0
        for f in feature_result[
            "overlapping_features"
        ]
    ),
    "All overlapping features have distance 0",
)

check(
    all(
        f.distance_to_variant > 0
        for f in feature_result[
            "nearby_features"
        ]
    ),
    "Nearby features have positive distance",
)

check(
    calculate_feature_distance(
        50,
        40,
        60,
    ) == 0,
    "Inside-feature distance logic correct",
)

check(
    calculate_feature_distance(
        30,
        40,
        60,
    ) == 10,
    "Before-feature distance logic correct",
)

check(
    calculate_feature_distance(
        70,
        40,
        60,
    ) == 10,
    "After-feature distance logic correct",
)


# ============================================================
# 7. Visualization payload
# ============================================================

print("\n7. Visualization payload")

visualization = build_protein_visualization(
    "TP53",
    248,
    "R",
    "H",
)

verify_visualization_payload(
    visualization
)

check(
    isinstance(
        visualization,
        ProteinContextResult,
    ),
    "Visualization returns ProteinContextResult",
)

check(
    visualization.variant_marker.label
    == "R248H",
    "Variant marker created",
)

check(
    len(
        visualization.visualization_tracks
    ) > 0,
    "Visualization tracks created",
)

check(
    (
        0.0
        < visualization.variant[
            "normalized_position"
        ]
        <= 1.0
    ),
    "Variant normalized coordinate valid",
)

check(
    normalize_position(
        248,
        393,
    )
    == visualization.variant[
        "normalized_position"
    ],
    "Normalized coordinate deterministic",
)


# ============================================================
# 8. Contract / metadata
# ============================================================

print("\n8. Contract and metadata")

validate_protein_context_contract(
    visualization
)

payload = visualization.to_dict()

required_keys = {
    "protein",
    "variant",
    "sequence_context",
    "overlapping_features",
    "nearby_features",
    "visualization_tracks",
    "variant_marker",
    "protein_context_version",
    "visualization_version",
    "interpretation",
    "research_only",
    "disclaimer",
}

check(
    required_keys.issubset(
        payload.keys()
    ),
    "Required payload keys present",
)

check(
    payload[
        "protein_context_version"
    ] == PROTEIN_CONTEXT_VERSION,
    "Protein context version correct",
)

check(
    payload[
        "visualization_version"
    ] == PROTEIN_VISUALIZATION_VERSION,
    "Visualization version correct",
)

check(
    payload[
        "research_only"
    ] is True,
    "Research-only guard preserved",
)

check(
    bool(
        payload[
            "disclaimer"
        ]
    ),
    "Safety disclaimer present",
)


# ============================================================
# Final result
# ============================================================

print("\n" + "=" * 80)

print(
    f"PASSED: {passed}"
)

print(
    f"FAILED: {failed}"
)

print("=" * 80)

if failed == 0:

    print(
        "\n✅ SPRINT 6 FINAL VERIFICATION PASSED"
    )

else:

    raise SystemExit(
        "\n❌ SPRINT 6 FINAL VERIFICATION FAILED"
    )