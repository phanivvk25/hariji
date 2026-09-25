"""Google Gemini Provider implementation."""

import json
from typing import List, Optional, AsyncIterator, Dict, Any
from src.core.models import ChatMessage, ToolDefinition, ToolCall, LLMResponse
from src.core.providers.base import BaseLLMProvider, BaseEmbeddingProvider

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GoogleProvider(BaseLLMProvider):
    """Provider for Google Gemini models."""

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model_name, **kwargs)
        self.api_key = api_key
        if GENAI_AVAILABLE and api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    @property
    def provider_name(self) -> str:
        return "google"

    def _convert_messages_to_prompt_and_contents(self, messages: List[ChatMessage]):
        system_instruction = None
        contents = []

        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            elif m.role == "user":
                contents.append(f"User: {m.content}")
            elif m.role == "assistant":
                contents.append(f"Assistant: {m.content}")
            elif m.role == "tool":
                contents.append(f"Tool Output ({m.name or 'tool'}): {m.content}")

        combined_text = "\n\n".join(contents)
        return system_instruction, combined_text

    async def generate(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        if not self.client:
            # Mock / graceful fallback if API key not set
            return LLMResponse(
                content="[Google Gemini Provider is initialized. Please set your GEMINI_API_KEY in .env to execute live queries.]",
                tool_calls=[],
                provider=self.provider_name,
                model=self.model_name
            )

        system_instruction, prompt = self._convert_messages_to_prompt_and_contents(messages)

        config_args: Dict[str, Any] = {"temperature": temperature}
        if system_instruction:
            config_args["system_instruction"] = system_instruction
        if max_tokens:
            config_args["max_output_tokens"] = max_tokens

        config = types.GenerateContentConfig(**config_args)

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )

        return LLMResponse(
            content=response.text or "",
            tool_calls=[],
            provider=self.provider_name,
            model=self.model_name,
            usage={"total_tokens": getattr(response.usage_metadata, "total_token_count", 0)}
        )

    async def stream(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        if not self.client:
            yield "[Google Gemini Provider: Please set your GEMINI_API_KEY in .env.]"
            return

        system_instruction, prompt = self._convert_messages_to_prompt_and_contents(messages)
        config = types.GenerateContentConfig(temperature=temperature)

        response_stream = await self.client.aio.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=config
        )
        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text


class GoogleEmbeddingProvider(BaseEmbeddingProvider):
    """Google Gemini Embedding Provider."""

    def __init__(
        self,
        model_name: str = "text-embedding-004",
        api_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model_name, **kwargs)
        self.api_key = api_key
        if GENAI_AVAILABLE and api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    @property
    def provider_name(self) -> str:
        return "google"

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.client or not texts:
            # Fallback zero-vector if unconfigured
            return [[0.0] * 768 for _ in texts]
        
        embeddings = []
        for text in texts:
            res = await self.client.aio.models.embed_content(
                model=self.model_name,
                contents=text
            )
            embeddings.append(res.embedding.values)
        return embeddings

    async def embed_query(self, text: str) -> List[float]:
        res = await self.embed_documents([text])
        return res[0]
