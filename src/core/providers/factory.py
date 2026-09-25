"""Provider Factory for dynamically instantiating LLM and Embedding services."""

from typing import Optional, Dict, Any, List
from src.config import settings, ProviderType
from src.core.providers.base import BaseLLMProvider, BaseEmbeddingProvider
from src.core.providers.google_provider import GoogleProvider, GoogleEmbeddingProvider
from src.core.providers.openai_provider import OpenAIProvider, OpenAIEmbeddingProvider
from src.core.providers.azure_provider import AzureOpenAIProvider, AzureOpenAIEmbeddingProvider
from src.core.providers.bedrock_provider import BedrockProvider, BedrockEmbeddingProvider


class MockLLMProvider(BaseLLMProvider):
    """Fallback mock provider for zero-config offline testing."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(self, messages, tools=None, temperature=0.2, max_tokens=None, **kwargs):
        from src.core.models import LLMResponse, ToolCall
        last_message = messages[-1].content if messages else "Hello"
        
        # Check if user asked for a calculation or knowledge lookup
        if "calculate" in last_message.lower() or "+" in last_message or "*" in last_message:
            tool_calls = [ToolCall(id="calc_1", name="calculator", arguments={"expression": "128 * 4"})]
            return LLMResponse(
                content="I need to calculate this result.",
                tool_calls=tool_calls,
                provider=self.provider_name,
                model=self.model_name
            )

        return LLMResponse(
            content=f"[Agent Response via {self.model_name}] I processed your query: '{last_message[:60]}...'. All multi-agent and RAG capabilities are operational.",
            tool_calls=[],
            provider=self.provider_name,
            model=self.model_name
        )

    async def stream(self, messages, tools=None, temperature=0.2, max_tokens=None, **kwargs):
        res = await self.generate(messages, tools, temperature, max_tokens, **kwargs)
        for word in res.content.split():
            yield word + " "


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Fallback embedding provider returning normalized pseudo-embeddings."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        import hashlib
        vectors = []
        for text in texts:
            # Deterministic hash pseudo-embedding of length 128
            h = hashlib.sha256(text.encode()).digest()
            vec = [(float(b) - 128.0) / 128.0 for b in h[:32]] * 4
            vectors.append(vec)
        return vectors

    async def embed_query(self, text: str) -> List[float]:
        res = await self.embed_documents([text])
        return res[0]


class ProviderFactory:
    """Manages active LLM and Embedding providers with runtime switching."""

    _active_llm_provider: Optional[BaseLLMProvider] = None
    _active_embedding_provider: Optional[BaseEmbeddingProvider] = None

    @classmethod
    def get_llm_provider(
        cls,
        provider_type: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        p_type = (provider_type or settings.DEFAULT_LLM_PROVIDER).lower()

        if p_type in ["google", "gemini"]:
            key = kwargs.get("api_key") or settings.GEMINI_API_KEY
            m_name = model_name or settings.GEMINI_MODEL
            if key:
                return GoogleProvider(model_name=m_name, api_key=key, **kwargs)

        elif p_type in ["openai", "custom"]:
            key = kwargs.get("api_key") or settings.OPENAI_API_KEY
            m_name = model_name or settings.OPENAI_MODEL
            base_url = kwargs.get("base_url") or settings.OPENAI_BASE_URL
            if key or base_url:
                return OpenAIProvider(model_name=m_name, api_key=key, base_url=base_url, **kwargs)

        elif p_type in ["azure", "microsoft", "azure_openai"]:
            key = kwargs.get("api_key") or settings.AZURE_OPENAI_API_KEY
            endpoint = kwargs.get("azure_endpoint") or settings.AZURE_OPENAI_ENDPOINT
            deployment = model_name or settings.AZURE_OPENAI_DEPLOYMENT_NAME
            if key and endpoint:
                return AzureOpenAIProvider(
                    deployment_name=deployment,
                    api_key=key,
                    azure_endpoint=endpoint,
                    api_version=kwargs.get("api_version") or settings.AZURE_OPENAI_API_VERSION
                )

        elif p_type in ["aws_bedrock", "bedrock", "amazon"]:
            m_name = model_name or settings.AWS_BEDROCK_MODEL_ID
            return BedrockProvider(
                model_name=m_name,
                aws_access_key_id=kwargs.get("aws_access_key_id") or settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=kwargs.get("aws_secret_access_key") or settings.AWS_SECRET_ACCESS_KEY,
                region_name=kwargs.get("region_name") or settings.AWS_REGION
            )

        # Fallback to Mock provider for immediate offline demo/test if credentials are absent
        return MockLLMProvider(model_name=model_name or "mock-agent-model")

    @classmethod
    def get_embedding_provider(
        cls,
        provider_type: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs
    ) -> BaseEmbeddingProvider:
        p_type = (provider_type or settings.DEFAULT_EMBEDDING_PROVIDER).lower()

        if p_type in ["google", "gemini"]:
            key = kwargs.get("api_key") or settings.GEMINI_API_KEY
            if key:
                return GoogleEmbeddingProvider(
                    model_name=model_name or settings.GEMINI_EMBEDDING_MODEL,
                    api_key=key
                )

        elif p_type in ["openai", "custom"]:
            key = kwargs.get("api_key") or settings.OPENAI_API_KEY
            if key:
                return OpenAIEmbeddingProvider(
                    model_name=model_name or settings.OPENAI_EMBEDDING_MODEL,
                    api_key=key,
                    base_url=kwargs.get("base_url") or settings.OPENAI_BASE_URL
                )

        elif p_type in ["azure", "microsoft", "azure_openai"]:
            key = kwargs.get("api_key") or settings.AZURE_OPENAI_API_KEY
            endpoint = kwargs.get("azure_endpoint") or settings.AZURE_OPENAI_ENDPOINT
            if key and endpoint:
                return AzureOpenAIEmbeddingProvider(
                    deployment_name=model_name or settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                    api_key=key,
                    azure_endpoint=endpoint
                )

        elif p_type in ["aws_bedrock", "bedrock", "amazon"]:
            return BedrockEmbeddingProvider(
                model_name=model_name or settings.AWS_BEDROCK_EMBEDDING_MODEL_ID,
                aws_access_key_id=kwargs.get("aws_access_key_id") or settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=kwargs.get("aws_secret_access_key") or settings.AWS_SECRET_ACCESS_KEY,
                region_name=kwargs.get("region_name") or settings.AWS_REGION
            )

        return MockEmbeddingProvider(model_name=model_name or "mock-embedder")
