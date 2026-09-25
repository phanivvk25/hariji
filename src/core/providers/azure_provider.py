"""Microsoft Azure OpenAI Provider implementation."""

import json
from typing import List, Optional, AsyncIterator, Dict, Any
from src.core.models import ChatMessage, ToolDefinition, ToolCall, LLMResponse
from src.core.providers.base import BaseLLMProvider, BaseEmbeddingProvider

try:
    from openai import AsyncAzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False


class AzureOpenAIProvider(BaseLLMProvider):
    """Provider for Microsoft Azure OpenAI Service."""

    def __init__(
        self,
        deployment_name: str,
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        api_version: str = "2024-06-01",
        **kwargs
    ):
        super().__init__(model_name=deployment_name, **kwargs)
        if not AZURE_OPENAI_AVAILABLE:
            raise ImportError("openai package is required for Azure OpenAI. Install via `pip install openai`.")
        self.deployment_name = deployment_name
        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )

    @property
    def provider_name(self) -> str:
        return "azure"

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
        azure_tools = self._convert_tools(tools)
        formatted_messages = self._convert_messages(messages)

        request_kwargs: Dict[str, Any] = {
            "model": self.deployment_name,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        if max_tokens:
            request_kwargs["max_tokens"] = max_tokens
        if azure_tools:
            request_kwargs["tools"] = azure_tools

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
            model=self.deployment_name,
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
            model=self.deployment_name,
            messages=formatted_messages,
            temperature=temperature,
            stream=True
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else ""
            if delta:
                yield delta


class AzureOpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Microsoft Azure OpenAI Embeddings provider."""

    def __init__(
        self,
        deployment_name: str,
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        api_version: str = "2024-06-01",
        **kwargs
    ):
        super().__init__(model_name=deployment_name, **kwargs)
        if not AZURE_OPENAI_AVAILABLE:
            raise ImportError("openai package is required for Azure OpenAI.")
        self.deployment_name = deployment_name
        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version
        )

    @property
    def provider_name(self) -> str:
        return "azure"

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        res = await self.client.embeddings.create(input=texts, model=self.deployment_name)
        return [item.embedding for item in res.data]

    async def embed_query(self, text: str) -> List[float]:
        res = await self.client.embeddings.create(input=[text], model=self.deployment_name)
        return res.data[0].embedding
