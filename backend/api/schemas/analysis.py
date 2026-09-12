from pydantic import BaseModel

from backend.api.schemas.prediction import (
    PredictionResult,
)

from backend.api.schemas.protein import (
    ProteinContextResponse,
)

from backend.api.schemas.scientist import (
    ScientistResponse,
)

from backend.api.schemas.variant import (
    VariantIdentity,
    VariantValidationResponse,
)

from backend.api.schemas.xai import (
    XAIResponse,
)


# ============================================================
# Complete GeneMirror analysis response
# ============================================================

class UnifiedAnalysisResponse(
    BaseModel
):

    success: bool = True

    variant: VariantIdentity

    validation: (
        VariantValidationResponse
    )

    prediction: (
        PredictionResult
    )

    xai: (
        XAIResponse
    )

    protein_context: (
        ProteinContextResponse
    )

    scientist: (
        ScientistResponse
    )

    research_only: bool = True

    disclaimer: str