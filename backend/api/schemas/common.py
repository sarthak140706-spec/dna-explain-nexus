from typing import Optional

from pydantic import BaseModel, Field


class APIMessage(BaseModel):
    message: str


class APIErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class APIErrorResponse(BaseModel):
    success: bool = False
    error: APIErrorDetail


class ResearchMetadata(BaseModel):
    research_only: bool = True

    disclaimer: str = Field(
        default=(
            "GeneMirror AI provides computational "
            "predictions for research and educational "
            "purposes only. It does not provide "
            "clinical diagnosis, treatment "
            "recommendations, or medical advice."
        )
    )