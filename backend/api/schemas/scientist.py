from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

from backend.api.schemas.variant import (
    VariantIdentity,
)


# ============================================================
# Scientist explanation sections
# ============================================================

class ScientistSectionsResponse(
    BaseModel
):

    overview: str

    prediction: str

    evidence: str

    protein_context: str

    limitations: str


# ============================================================
# Scientist execution metadata
# ============================================================

class ScientistExecutionMetadata(
    BaseModel
):

    requested_provider: Optional[
        str
    ] = None

    provider_used: str

    used_llm_response: bool

    fallback_used: bool

    fallback_reason: Optional[
        str
    ] = None

    validation_errors: List[
        str
    ] = Field(
        default_factory=list,
    )


# ============================================================
# Complete Scientist response
# ============================================================

class ScientistResponse(
    BaseModel
):

    success: bool = True

    variant: VariantIdentity

    sections: ScientistSectionsResponse

    grounded_facts: List[
        Dict[str, Any]
    ] = Field(
        default_factory=list,
    )

    scientist_name: str

    scientist_version: str

    contract_version: str

    provider: str

    language_model: Optional[
        str
    ] = None

    execution: (
        ScientistExecutionMetadata
    )

    research_only: bool = True

    disclaimer: str