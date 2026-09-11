import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


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

from backend.protein_context.config import (
    SUPPORTED_AMINO_ACIDS,
    SUPPORTED_FEATURE_TYPES,
)

from backend.protein_context.contracts import (
    ProteinFeature,
    ProteinIdentity,
)

from backend.protein_context.uniprot_client import (
    get_reviewed_human_protein,
)


# ============================================================
# Protein name parser
# ============================================================

def parse_protein_name(
    entry: Dict[str, Any],
) -> str:

    protein_description = entry.get(
        "proteinDescription",
        {},
    )

    recommended_name = protein_description.get(
        "recommendedName",
        {},
    )

    full_name = recommended_name.get(
        "fullName",
        {},
    )

    value = full_name.get(
        "value"
    )

    if value:

        return str(value)

    submission_names = protein_description.get(
        "submissionNames",
        [],
    )

    if submission_names:

        first = submission_names[0]

        value = (
            first.get(
                "fullName",
                {},
            ).get(
                "value"
            )
        )

        if value:

            return str(value)

    return "Unknown protein"


# ============================================================
# Sequence parser
# ============================================================

def parse_sequence(
    entry: Dict[str, Any],
) -> str:

    sequence = (
        entry.get(
            "sequence",
            {},
        ).get(
            "value"
        )
    )

    if not sequence:

        raise ValueError(
            "UniProt entry contains "
            "no protein sequence."
        )

    sequence = (
        str(sequence)
        .strip()
        .upper()
    )

    invalid = set(
        sequence
    ) - SUPPORTED_AMINO_ACIDS

    if invalid:

        raise ValueError(
            "Protein sequence contains "
            "unsupported amino acids: "
            f"{sorted(invalid)}"
        )

    return sequence


# ============================================================
# Sequence length
# ============================================================

def parse_sequence_length(
    entry: Dict[str, Any],
    sequence: Optional[str] = None,
) -> int:

    if sequence is None:

        sequence = parse_sequence(
            entry
        )

    reported_length = (
        entry.get(
            "sequence",
            {},
        ).get(
            "length"
        )
    )

    actual_length = len(
        sequence
    )

    if reported_length is None:

        return actual_length

    reported_length = int(
        reported_length
    )

    if (
        reported_length
        != actual_length
    ):

        raise ValueError(
            "Reported UniProt sequence length "
            "does not match sequence value."
        )

    return actual_length


# ============================================================
# Gene symbol extraction
# ============================================================

def parse_gene_symbol(
    entry: Dict[str, Any],
) -> str:

    genes = entry.get(
        "genes",
        [],
    )

    for gene in genes:

        gene_name = (
            gene.get(
                "geneName",
                {},
            ).get(
                "value"
            )
        )

        if gene_name:

            return (
                str(
                    gene_name
                )
                .strip()
                .upper()
            )

    raise ValueError(
        "UniProt entry contains "
        "no primary gene symbol."
    )


# ============================================================
# Reviewed status
# ============================================================

def parse_reviewed_status(
    entry: Dict[str, Any],
) -> bool:

    entry_type = str(
        entry.get(
            "entryType",
            ""
        )
    ).lower()

    return (
        "reviewed"
        in entry_type
        and "unreviewed"
        not in entry_type
    )


# ============================================================
# Protein identity
# ============================================================

def parse_protein_identity(
    entry: Dict[str, Any],
) -> ProteinIdentity:

    sequence = parse_sequence(
        entry
    )

    sequence_length = (
        parse_sequence_length(
            entry,
            sequence,
        )
    )

    accession = entry.get(
        "primaryAccession"
    )

    if not accession:

        raise ValueError(
            "UniProt entry contains "
            "no primary accession."
        )

    organism = (
        entry.get(
            "organism",
            {},
        ).get(
            "scientificName"
        )
    )

    if not organism:

        organism = (
            "Unknown organism"
        )

    return ProteinIdentity(
        accession=str(
            accession
        ),
        gene_symbol=(
            parse_gene_symbol(
                entry
            )
        ),
        protein_name=(
            parse_protein_name(
                entry
            )
        ),
        organism=str(
            organism
        ),
        sequence_length=(
            sequence_length
        ),
        reviewed=(
            parse_reviewed_status(
                entry
            )
        ),
        entry_name=(
            entry.get(
                "uniProtkbId"
            )
        ),
        source="UniProtKB",
    )


# ============================================================
# Feature position helpers
# ============================================================

def parse_feature_position(
    location: Dict[str, Any],
    key: str,
) -> Optional[int]:

    container = location.get(
        key,
        {},
    )

    value = container.get(
        "value"
    )

    if value is None:

        return None

    try:

        value = int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if value <= 0:

        return None

    return value


# ============================================================
# Feature evidence parser
# ============================================================

def parse_feature_evidence(
    feature: Dict[str, Any],
) -> List[str]:

    evidence_values = []

    for evidence in feature.get(
        "evidences",
        [],
    ):

        if not isinstance(
            evidence,
            dict,
        ):

            continue

        evidence_code = (
            evidence.get(
                "evidenceCode"
            )
        )

        source = evidence.get(
            "source"
        )

        evidence_id = evidence.get(
            "id"
        )

        pieces = []

        if evidence_code:

            pieces.append(
                str(
                    evidence_code
                )
            )

        if source:

            pieces.append(
                str(
                    source
                )
            )

        if evidence_id:

            pieces.append(
                str(
                    evidence_id
                )
            )

        if pieces:

            evidence_values.append(
                " | ".join(
                    pieces
                )
            )

    return evidence_values


# ============================================================
# Individual feature parser
# ============================================================

def parse_feature(
    feature: Dict[str, Any],
    protein_length: int,
) -> Optional[ProteinFeature]:

    feature_type = feature.get(
        "type"
    )

    if (
        feature_type
        not in SUPPORTED_FEATURE_TYPES
    ):

        return None

    location = feature.get(
        "location",
        {},
    )

    start = parse_feature_position(
        location,
        "start",
    )

    end = parse_feature_position(
        location,
        "end",
    )

    if start is None:

        return None

    if end is None:

        end = start

    if (
        start > end
        or end > protein_length
    ):

        return None

    description = feature.get(
        "description"
    )

    feature_id = (
        feature.get(
            "featureId"
        )
    )

    return ProteinFeature(
        feature_type=str(
            feature_type
        ),
        start=int(
            start
        ),
        end=int(
            end
        ),
        description=(
            str(
                description
            )
            if description
            else None
        ),
        feature_id=(
            str(
                feature_id
            )
            if feature_id
            else None
        ),
        evidence=(
            parse_feature_evidence(
                feature
            )
        ),
    )


# ============================================================
# Parse all supported features
# ============================================================

def parse_protein_features(
    entry: Dict[str, Any],
    protein_length: int,
) -> List[ProteinFeature]:

    parsed_features = []

    for feature in entry.get(
        "features",
        [],
    ):

        if not isinstance(
            feature,
            dict,
        ):

            continue

        parsed = parse_feature(
            feature,
            protein_length,
        )

        if parsed is not None:

            parsed_features.append(
                parsed
            )

    parsed_features.sort(
        key=lambda item: (
            item.start,
            item.end,
            item.feature_type,
        )
    )

    return parsed_features


# ============================================================
# Complete entry parser
# ============================================================

def parse_uniprot_entry(
    entry: Dict[str, Any],
) -> Dict[str, Any]:

    identity = (
        parse_protein_identity(
            entry
        )
    )

    sequence = (
        parse_sequence(
            entry
        )
    )

    features = (
        parse_protein_features(
            entry,
            identity.sequence_length,
        )
    )

    return {
        "identity": identity,
        "sequence": sequence,
        "features": features,
        "feature_count": len(
            features
        ),
    }


# ============================================================
# Verification
# ============================================================

def verify_parsed_protein(
    parsed: Dict[str, Any],
) -> None:

    identity = parsed[
        "identity"
    ]

    sequence = parsed[
        "sequence"
    ]

    features = parsed[
        "features"
    ]

    if not identity.accession:

        raise ValueError(
            "Parsed accession missing."
        )

    if not identity.gene_symbol:

        raise ValueError(
            "Parsed gene symbol missing."
        )

    if not identity.reviewed:

        raise ValueError(
            "Protein entry is not reviewed."
        )

    if (
        identity.organism
        != "Homo sapiens"
    ):

        raise ValueError(
            "Protein is not human."
        )

    if (
        identity.sequence_length
        != len(
            sequence
        )
    ):

        raise ValueError(
            "Protein length mismatch."
        )

    for feature in features:

        if not (
            1
            <= feature.start
            <= feature.end
            <= identity.sequence_length
        ):

            raise ValueError(
                "Parsed protein feature "
                "has invalid coordinates."
            )


# ============================================================
# CLI smoke test
# ============================================================

def main():

    print(
        "GeneMirror Sprint 6 "
        "Protein Sequence & Feature Parser"
    )

    print(
        "=" * 72
    )

    gene_symbol = "TP53"

    print(
        f"\nLoading protein: "
        f"{gene_symbol}"
    )

    result = (
        get_reviewed_human_protein(
            gene_symbol
        )
    )

    parsed = (
        parse_uniprot_entry(
            result[
                "entry"
            ]
        )
    )

    verify_parsed_protein(
        parsed
    )

    identity = parsed[
        "identity"
    ]

    print(
        f"Accession: "
        f"{identity.accession}"
    )

    print(
        f"Gene: "
        f"{identity.gene_symbol}"
    )

    print(
        f"Protein: "
        f"{identity.protein_name}"
    )

    print(
        f"Organism: "
        f"{identity.organism}"
    )

    print(
        f"Reviewed: "
        f"{identity.reviewed}"
    )

    print(
        f"Sequence length: "
        f"{identity.sequence_length}"
    )

    print(
        f"Feature count: "
        f"{parsed['feature_count']}"
    )

    print(
        "\nFirst 10 parsed features"
    )

    print(
        "-" * 72
    )

    for feature in (
        parsed[
            "features"
        ][
            :10
        ]
    ):

        print(
            f"{feature.feature_type:20} "
            f"{feature.start:4}-"
            f"{feature.end:<4} "
            f"{feature.description}"
        )

    print(
        "\n✅ Protein parser completed."
    )


if __name__ == "__main__":
    main()