"""OpenAI and OpenAI-compatible Provider implementation."""

import json
from typing import List, Optional, AsyncIterator, Dict, Any
from src.core.models import ChatMessage, ToolDefinition, ToolCall, LLMResponse
from src.core.providers.base import BaseLLMProvider, BaseEmbeddingProvider

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseLLMProvider):
    """Provider for standard OpenAI models and compatible endpoints."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model_name, **kwargs)
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package is required. Install via `pip install openai`.")
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    @property
    def provider_name(self) -> str:
        return "openai"

    def _convert_tools(self, tools: Optional[List[ToolDefinition]]) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters
                }
            }
            for t in tools
        ]

    def _convert_messages(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        formatted = []
        for m in messages:
            msg: Dict[str, Any] = {"role": m.role, "content": m.content}
            if m.name:
                msg["name"] = m.name
            if m.tool_calls:
                msg["tool_calls"] = m.tool_calls
            if m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            formatted.append(msg)
        return formatted

    async def generate(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        openai_tools = self._convert_tools(tools)
        formatted_messages = self._convert_messages(messages)

        request_kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        if max_tokens:
            request_kwargs["max_tokens"] = max_tokens
        if openai_tools:
            request_kwargs["tools"] = openai_tools

        response = await self.client.chat.completions.create(**request_kwargs)
        choice = response.choices[0]
        tool_calls: List[ToolCall] = []

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                args = {}
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {"raw": tc.function.arguments}
                tool_calls.append(
                    ToolCall(id=tc.id, name=tc.function.name, arguments=args)
                )

        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            provider=self.provider_name,
            model=self.model_name,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason
        )

    async def stream(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        formatted_messages = self._convert_messages(messages)
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=formatted_messages,
            temperature=temperature,
            stream=True
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else ""
            if delta:
                yield delta


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI Embedding generation provider."""

    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model_name, **kwargs)
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package is required. Install via `pip install openai`.")
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        res = await self.client.embeddings.create(input=texts, model=self.model_name)
        return [item.embedding for item in res.data]

    async def embed_query(self, text: str) -> List[float]:
        res = await self.client.embeddings.create(input=[text], model=self.model_name)
        return res.data[0].embedding
