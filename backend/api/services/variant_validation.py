import sys
from pathlib import Path
from typing import Any, Dict


# ============================================================
# Sprint 3 compatibility path
# ============================================================
#
# The frozen Sprint 3 annotation modules use local imports
# such as:
#
#     from vep_client import ...
#     from parser import ...
#     from transcript_selector import ...
#
# When imported through FastAPI as backend.annotation.*,
# Python does not automatically treat backend/annotation
# as a top-level import location.
#
# We therefore add the frozen annotation directory to
# sys.path here instead of modifying Sprint 3 code.
# ============================================================

CURRENT_FILE = Path(__file__).resolve()

BACKEND_DIR = (
    CURRENT_FILE.parents[2]
)

ANNOTATION_DIR = (
    BACKEND_DIR
    / "annotation"
)

if str(ANNOTATION_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ANNOTATION_DIR),
    )


# ============================================================
# Existing GeneMirror scientific engines
# ============================================================

from backend.annotation.annotator import (
    annotate_variant,
)

from backend.protein_context.variant_validator import (
    ProteinVariantValidationError,
    validate_variant_for_gene,
)


# ============================================================
# API schemas
# ============================================================

from backend.api.schemas.variant import (
    GenomicValidationResult,
    ProteinValidationResult,
    VariantIdentity,
    VariantRequest,
    VariantValidationResponse,
)


# ============================================================
# Constants
# ============================================================

RESEARCH_DISCLAIMER = (
    "GeneMirror AI provides computational predictions "
    "for research and educational purposes only. "
    "It does not provide clinical diagnosis, treatment "
    "recommendations, or medical advice."
)


# ============================================================
# Service exceptions
# ============================================================

class VariantValidationServiceError(
    RuntimeError
):
    """
    Raised when a required external scientific
    service cannot complete validation.
    """


# ============================================================
# Identity adapter
# ============================================================

def build_variant_identity(
    request: VariantRequest,
) -> VariantIdentity:

    return VariantIdentity(
        gene_symbol=(
            request.gene_symbol
        ),
        chromosome=(
            request.chromosome
        ),
        position=(
            request.position
        ),
        reference_allele=(
            request.reference_allele
        ),
        alternate_allele=(
            request.alternate_allele
        ),
        protein_position=(
            request.protein_position
        ),
        reference_amino_acid=(
            request.reference_amino_acid
        ),
        alternate_amino_acid=(
            request.alternate_amino_acid
        ),
        dna_change=(
            request.dna_change
        ),
        protein_change=(
            request.protein_change
        ),
    )


# ============================================================
# Protein validation adapter
# ============================================================

def run_protein_validation(
    request: VariantRequest,
) -> ProteinValidationResult:

    try:

        result = (
            validate_variant_for_gene(
                gene_symbol=(
                    request.gene_symbol
                ),
                protein_position=(
                    request.protein_position
                ),
                reference_aa=(
                    request.reference_amino_acid
                ),
                alternate_aa=(
                    request.alternate_amino_acid
                ),
            )
        )

        return ProteinValidationResult(
            performed=True,
            valid=True,
            accession=(
                result.get(
                    "accession"
                )
            ),
            protein_name=(
                result.get(
                    "protein_name"
                )
            ),
            reviewed=(
                result.get(
                    "reviewed"
                )
            ),
            protein_length=(
                result.get(
                    "protein_length"
                )
            ),
            sequence_reference_amino_acid=(
                result.get(
                    "sequence_reference_amino_acid"
                )
            ),
            position_matches_reference=(
                result.get(
                    "position_matches_reference"
                )
            ),
            amino_acid_change=(
                result.get(
                    "amino_acid_change"
                )
            ),
            source=(
                result.get(
                    "source"
                )
            ),
            validation_status=(
                result.get(
                    "reference_validation",
                    "matched",
                )
            ),
            error=None,
        )

    except ProteinVariantValidationError as error:

        return ProteinValidationResult(
            performed=True,
            valid=False,
            validation_status=(
                "protein_validation_failed"
            ),
            error=str(
                error
            ),
        )

    except Exception as error:

        raise VariantValidationServiceError(
            "Protein validation service "
            f"failed: {error}"
        ) from error


# ============================================================
# Genomic validation adapter
# ============================================================

def run_genomic_validation(
    request: VariantRequest,
) -> GenomicValidationResult:

    # Genomic validation is optional because
    # some API calls may provide only the
    # protein-level substitution.

    if (
        request.chromosome is None
        or request.position is None
    ):

        return GenomicValidationResult(
            performed=False,
            valid=None,
            annotation_status=(
                "not_requested"
            ),
        )

    try:

        result: Dict[
            str,
            Any,
        ] = annotate_variant(
            chromosome=(
                request.chromosome
            ),
            position=(
                request.position
            ),
            reference=(
                request.reference_allele
            ),
            alternate=(
                request.alternate_allele
            ),
            gene_symbol=(
                request.gene_symbol
            ),
            source_dna_change=(
                request.dna_change
            ),
            source_protein_change=(
                request.protein_change
            ),
        )

    except Exception as error:

        raise VariantValidationServiceError(
            "Genomic annotation service "
            f"failed: {error}"
        ) from error

    annotation_status = (
        result.get(
            "annotation_status"
        )
    )

    is_missense = bool(
        result.get(
            "is_missense",
            False,
        )
    )

    genomic_valid = (
        annotation_status
        == "annotated"
        and is_missense
    )

    return GenomicValidationResult(
        performed=True,
        valid=genomic_valid,
        annotation_status=(
            annotation_status
        ),
        most_severe_consequence=(
            result.get(
                "most_severe_consequence"
            )
        ),
        transcript_id=(
            result.get(
                "transcript_id"
            )
        ),
        consequence_terms=(
            result.get(
                "consequence_terms"
            )
        ),
        is_missense=(
            result.get(
                "is_missense"
            )
        ),
        mane_select=(
            result.get(
                "mane_select"
            )
        ),
        canonical=(
            result.get(
                "canonical"
            )
        ),
        vep_dna_change=(
            result.get(
                "vep_dna_change"
            )
        ),
        vep_protein_change=(
            result.get(
                "vep_protein_change"
            )
        ),
        dna_match=(
            result.get(
                "dna_match"
            )
        ),
        protein_match=(
            result.get(
                "protein_match"
            )
        ),
        verification_status=(
            result.get(
                "verification_status"
            )
        ),
        selection_reason=(
            result.get(
                "selection_reason"
            )
        ),
        error=None,
    )


# ============================================================
# Overall validation status
# ============================================================

def determine_overall_status(
    protein_validation: (
        ProteinValidationResult
    ),
    genomic_validation: (
        GenomicValidationResult
    ),
) -> tuple[
    bool,
    str,
]:

    # Protein validation is required for
    # GeneMirror V1 because the model expects
    # a missense amino-acid substitution.

    if not protein_validation.valid:

        return (
            False,
            "protein_validation_failed",
        )

    # If genomic validation was requested,
    # it must confirm a missense consequence.

    if genomic_validation.performed:

        if genomic_validation.valid is not True:

            return (
                False,
                "genomic_validation_failed",
            )

        return (
            True,
            "fully_validated",
        )

    return (
        True,
        "protein_validated",
    )


# ============================================================
# Main service
# ============================================================

def validate_variant_request(
    request: VariantRequest,
) -> VariantValidationResponse:

    variant = (
        build_variant_identity(
            request
        )
    )

    protein_validation = (
        run_protein_validation(
            request
        )
    )

    genomic_validation = (
        run_genomic_validation(
            request
        )
    )

    valid, status = (
        determine_overall_status(
            protein_validation=(
                protein_validation
            ),
            genomic_validation=(
                genomic_validation
            ),
        )
    )

    return VariantValidationResponse(
        success=True,
        variant=variant,
        valid=valid,
        validation_status=status,
        protein_validation=(
            protein_validation
        ),
        genomic_validation=(
            genomic_validation
        ),
        research_only=True,
        disclaimer=(
            RESEARCH_DISCLAIMER
        ),
    )