"""
GeneMirror API route modules.
"""

from backend.api.routes.variant import (
    router as variant_router,
)

from backend.api.routes.prediction import (
    router as prediction_router,
)

from backend.api.routes.xai import (
    router as xai_router,
)

from backend.api.routes.protein import (
    router as protein_router,
)

from backend.api.routes.scientist import (
    router as scientist_router,
)

from backend.api.routes.analysis import (
    router as analysis_router,
)


__all__ = [
    "variant_router",
    "prediction_router",
    "xai_router",
    "protein_router",
    "scientist_router",
    "analysis_router",
]