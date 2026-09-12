import json
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


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
# Provider configuration
# ============================================================

PROVIDER_ENVIRONMENT_VARIABLE = (
    "GENEMIRROR_SCIENTIST_PROVIDER"
)

DEFAULT_PROVIDER = "disabled"

SUPPORTED_PROVIDERS = (
    "disabled",
    "mock",
)


# ============================================================
# Exceptions
# ============================================================

class LLMProviderError(RuntimeError):
    """Base error for Scientist LLM providers."""


class LLMProviderUnavailableError(
    LLMProviderError
):
    """Raised when the selected provider cannot run."""


class UnsupportedLLMProviderError(
    LLMProviderError
):
    """Raised when an unknown provider is requested."""


# ============================================================
# Provider response
# ============================================================

@dataclass
class LLMProviderResponse:
    content: str

    provider_name: str

    model_name: Optional[str] = None

    raw_response: Optional[
        Dict[str, Any]
    ] = None

    used_external_service: bool = False

    def to_dict(self) -> Dict[str, Any]:

        return {
            "content": self.content,
            "provider_name": (
                self.provider_name
            ),
            "model_name": self.model_name,
            "raw_response": (
                self.raw_response
            ),
            "used_external_service": (
                self.used_external_service
            ),
        }


# ============================================================
# Provider interface
# ============================================================

class BaseLLMProvider(ABC):

    provider_name = "base"
    model_name = None

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        response_format: str = "json",
    ) -> LLMProviderResponse:

        raise NotImplementedError


# ============================================================
# Disabled provider
# ============================================================

class DisabledLLMProvider(
    BaseLLMProvider
):

    provider_name = "disabled"
    model_name = None

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        response_format: str = "json",
    ) -> LLMProviderResponse:

        raise LLMProviderUnavailableError(
            "No external language-model provider "
            "is currently enabled. GeneMirror "
            "Scientist should use its deterministic "
            "fallback explanation."
        )


# ============================================================
# Offline mock provider
# ============================================================

class MockLLMProvider(
    BaseLLMProvider
):

    provider_name = "mock"
    model_name = "GeneMirror-Mock-LLM"

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        response_format: str = "json",
    ) -> LLMProviderResponse:

        if not system_prompt.strip():
            raise LLMProviderError(
                "System prompt cannot be empty."
            )

        if not user_prompt.strip():
            raise LLMProviderError(
                "User prompt cannot be empty."
            )

        if temperature != 0.0:
            raise LLMProviderError(
                "GeneMirror mock provider expects "
                "temperature=0.0."
            )

        if response_format != "json":
            raise LLMProviderError(
                "GeneMirror mock provider expects "
                "JSON response format."
            )

        mock_payload = {
            "overview": (
                "This is a deterministic mock "
                "Scientist overview generated only "
                "for offline pipeline testing."
            ),
            "prediction": (
                "The prediction section is a mock "
                "response used to test the provider "
                "interface. No additional scientific "
                "claims are introduced."
            ),
            "evidence": (
                "The evidence section is a mock "
                "response used for software testing "
                "only."
            ),
            "protein_context": (
                "The protein-context section is a "
                "mock response used for software "
                "testing only."
            ),
            "limitations": (
                "This mock output is not a scientific "
                "interpretation and exists only to "
                "verify the GeneMirror Scientist "
                "provider interface."
            ),
        }

        content = json.dumps(
            mock_payload,
            ensure_ascii=False,
        )

        return LLMProviderResponse(
            content=content,
            provider_name=self.provider_name,
            model_name=self.model_name,
            raw_response={
                "mode": "offline_mock",
            },
            used_external_service=False,
        )


# ============================================================
# Provider-name normalization
# ============================================================

def normalize_provider_name(
    provider_name: Optional[str],
) -> str:

    if provider_name is None:

        provider_name = os.getenv(
            PROVIDER_ENVIRONMENT_VARIABLE,
            DEFAULT_PROVIDER,
        )

    normalized = (
        provider_name
        .strip()
        .lower()
    )

    if not normalized:
        normalized = DEFAULT_PROVIDER

    return normalized


# ============================================================
# Provider factory
# ============================================================

def create_llm_provider(
    provider_name: Optional[str] = None,
) -> BaseLLMProvider:

    normalized = normalize_provider_name(
        provider_name
    )

    if normalized == "disabled":

        return DisabledLLMProvider()

    if normalized == "mock":

        return MockLLMProvider()

    raise UnsupportedLLMProviderError(
        f"Unsupported GeneMirror Scientist "
        f"provider: {normalized}. "
        f"Supported providers: "
        f"{SUPPORTED_PROVIDERS}"
    )


# ============================================================
# Provider capability helper
# ============================================================

def provider_is_external(
    provider: BaseLLMProvider,
) -> bool:

    return provider.provider_name not in (
        "disabled",
        "mock",
    )


# ============================================================
# Verification helper
# ============================================================

def verify_provider_response(
    response: LLMProviderResponse,
) -> None:

    if not response.content.strip():

        raise ValueError(
            "Provider response content "
            "cannot be empty."
        )

    if not response.provider_name.strip():

        raise ValueError(
            "Provider name cannot be empty."
        )

    if not isinstance(
        response.used_external_service,
        bool,
    ):

        raise ValueError(
            "used_external_service must "
            "be boolean."
        )


# ============================================================
# CLI smoke test
# ============================================================

def main():

    from backend.scientist.contracts import (
        ScientistInput,
        ScientistPrediction,
        ScientistVariant,
    )

    from backend.scientist.prompt_builder import (
        build_prompt_package,
    )

    print(
        "GeneMirror Sprint 7 "
        "LLM Provider Interface"
    )

    print("=" * 72)

    variant = ScientistVariant(
        gene_symbol="TP53",
        protein_change="R248H",
    )

    prediction = ScientistPrediction(
        predicted_class=0,
        predicted_class_name="benign_like",
        raw_model_score=0.3944,
        calibrated_probability=0.2228,
        impact_class="MODERATE",
        confidence_score=0.2347,
        uncertainty_score=0.7653,
        confidence_band="LOW",
    )

    scientist_input = ScientistInput(
        variant=variant,
        prediction=prediction,
    )

    package = build_prompt_package(
        scientist_input
    )

    print(
        "\nSupported providers:",
        SUPPORTED_PROVIDERS,
    )

    print(
        "Default provider:",
        DEFAULT_PROVIDER,
    )

    print(
        "\nTesting mock provider"
    )

    print("-" * 72)

    provider = create_llm_provider(
        "mock"
    )

    response = provider.generate(
        system_prompt=(
            package["system_prompt"]
        ),
        user_prompt=(
            package["user_prompt"]
        ),
        temperature=(
            package["temperature"]
        ),
        response_format=(
            package["response_format"]
        ),
    )

    verify_provider_response(
        response
    )

    parsed = json.loads(
        response.content
    )

    print(
        "Provider:",
        response.provider_name,
    )

    print(
        "Model:",
        response.model_name,
    )

    print(
        "External service:",
        response.used_external_service,
    )

    print(
        "JSON sections:",
        list(parsed.keys()),
    )

    print(
        "\nTesting disabled provider"
    )

    print("-" * 72)

    disabled = create_llm_provider(
        "disabled"
    )

    try:

        disabled.generate(
            system_prompt=(
                package["system_prompt"]
            ),
            user_prompt=(
                package["user_prompt"]
            ),
            temperature=(
                package["temperature"]
            ),
            response_format=(
                package["response_format"]
            ),
        )

    except LLMProviderUnavailableError:

        print(
            "Disabled provider correctly "
            "requested deterministic fallback."
        )

    else:

        raise ValueError(
            "Disabled provider should not "
            "generate an LLM response."
        )

    print(
        "\n✅ LLM provider interface "
        "verification completed."
    )


if __name__ == "__main__":
    main()