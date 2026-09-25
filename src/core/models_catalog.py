"""Model Catalog and Dynamic Configuration Registry.
Provides model discovery, descriptions, parameter defaults, and runtime switching.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from src.config import settings


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: str
    context_window: int
    supports_vision: bool = False
    supports_tools: bool = True
    is_default: bool = False


class ProviderModelCatalog:
    """Catalog of known models per provider with support for custom models."""

    CATALOG: Dict[str, List[ModelInfo]] = {
        "google": [
            ModelInfo(
                id="gemini-2.5-flash",
                name="Gemini 2.5 Flash",
                provider="google",
                description="Google's ultra-fast, high-intelligence multimodal model for real-time agents.",
                context_window=1048576,
                supports_vision=True,
                is_default=True
            ),
            ModelInfo(
                id="gemini-2.5-pro",
                name="Gemini 2.5 Pro",
                provider="google",
                description="Google's premier model for complex multi-step reasoning and deep analysis.",
                context_window=2097152,
                supports_vision=True
            ),
            ModelInfo(
                id="gemini-1.5-flash",
                name="Gemini 1.5 Flash",
                provider="google",
                description="High throughput, low-latency versatile model.",
                context_window=1048576,
                supports_vision=True
            ),
            ModelInfo(
                id="gemini-1.5-pro",
                name="Gemini 1.5 Pro",
                provider="google",
                description="Advanced reasoning with 2M token context window.",
                context_window=2097152,
                supports_vision=True
            ),
        ],
        "openai": [
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                provider="openai",
                description="OpenAI's flagship omni model for multimodal reasoning and complex tasks.",
                context_window=128000,
                supports_vision=True,
                is_default=True
            ),
            ModelInfo(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                provider="openai",
                description="Fast, affordable small model for routine tasks and tool loops.",
                context_window=128000,
                supports_vision=True
            ),
            ModelInfo(
                id="o3-mini",
                name="o3-mini",
                provider="openai",
                description="High-reasoning math, science, and coding specialist.",
                context_window=200000,
                supports_vision=False
            ),
            ModelInfo(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                provider="openai",
                description="Previous flagship high-capability model.",
                context_window=128000,
                supports_vision=True
            ),
        ],
        "azure": [
            ModelInfo(
                id="gpt-4o",
                name="Azure GPT-4o Deployment",
                provider="azure",
                description="Enterprise Microsoft Azure OpenAI deployed endpoint for GPT-4o.",
                context_window=128000,
                supports_vision=True,
                is_default=True
            ),
            ModelInfo(
                id="gpt-4o-mini",
                name="Azure GPT-4o-mini Deployment",
                provider="azure",
                description="Cost-optimized Microsoft Azure OpenAI deployed endpoint.",
                context_window=128000,
                supports_vision=True
            ),
            ModelInfo(
                id="gpt-35-turbo",
                name="Azure GPT-3.5-Turbo",
                provider="azure",
                description="Legacy Azure deployment for quick lightweight tasks.",
                context_window=16384,
                supports_vision=False
            ),
        ],
        "aws_bedrock": [
            ModelInfo(
                id="anthropic.claude-3-5-sonnet-20240620-v1:0",
                name="Claude 3.5 Sonnet (Bedrock)",
                provider="aws_bedrock",
                description="State-of-the-art vision, reasoning, and coding on AWS Bedrock.",
                context_window=200000,
                supports_vision=True,
                is_default=True
            ),
            ModelInfo(
                id="anthropic.claude-3-haiku-20240307-v1:0",
                name="Claude 3 Haiku (Bedrock)",
                provider="aws_bedrock",
                description="Ultra-fast, compact Bedrock model for quick responses.",
                context_window=200000,
                supports_vision=True
            ),
            ModelInfo(
                id="amazon.titan-text-premier-v1:0",
                name="Amazon Titan Text Premier",
                provider="aws_bedrock",
                description="Amazon's high-performance native foundation model.",
                context_window=32000,
                supports_vision=False
            ),
            ModelInfo(
                id="meta.llama3-70b-instruct-v1:0",
                name="Meta Llama 3 70B (Bedrock)",
                provider="aws_bedrock",
                description="Open foundation model hosted on AWS Bedrock.",
                context_window=8000,
                supports_vision=False
            ),
        ]
    }

    # Current active runtime configuration
    _current_provider: str = settings.DEFAULT_LLM_PROVIDER
    _current_model: str = settings.GEMINI_MODEL

    @classmethod
    def get_available_providers(cls) -> List[Dict[str, Any]]:
        return [
            {"id": "google", "name": "Google Gemini", "default_model": settings.GEMINI_MODEL},
            {"id": "openai", "name": "OpenAI / Compatible", "default_model": settings.OPENAI_MODEL},
            {"id": "azure", "name": "Microsoft Azure OpenAI", "default_model": settings.AZURE_OPENAI_DEPLOYMENT_NAME},
            {"id": "aws_bedrock", "name": "Amazon AWS Bedrock", "default_model": settings.AWS_BEDROCK_MODEL_ID},
        ]

    @classmethod
    def get_models_for_provider(cls, provider: str) -> List[ModelInfo]:
        return cls.CATALOG.get(provider.lower(), [])

    @classmethod
    def get_active_selection(cls) -> Dict[str, str]:
        return {
            "provider": cls._current_provider,
            "model": cls._current_model
        }

    @classmethod
    def set_active_selection(cls, provider: str, model: str) -> Dict[str, str]:
        cls._current_provider = provider.lower()
        cls._current_model = model
        return cls.get_active_selection()


# Global catalog instance
model_catalog = ProviderModelCatalog()
