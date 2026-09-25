"""Amazon AWS Bedrock Provider implementation."""

import json
from typing import List, Optional, AsyncIterator, Dict, Any
from src.core.models import ChatMessage, ToolDefinition, ToolCall, LLMResponse
from src.core.providers.base import BaseLLMProvider, BaseEmbeddingProvider

try:
    import boto3
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False


class BedrockProvider(BaseLLMProvider):
    """Provider for Amazon Web Services (AWS) Bedrock models (e.g. Anthropic Claude, Amazon Nova/Titan)."""

    def __init__(
        self,
        model_name: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
        **kwargs
    ):
        super().__init__(model_name=model_name, **kwargs)
        self.region_name = region_name
        if BEDROCK_AVAILABLE and (aws_access_key_id or boto3.Session().get_credentials()):
            self.client = boto3.client(
                service_name="bedrock-runtime",
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
        else:
            self.client = None

    @property
    def provider_name(self) -> str:
        return "aws_bedrock"

    def _convert_messages(self, messages: List[ChatMessage]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        system_prompt = None
        formatted = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                formatted.append({
                    "role": "user" if m.role == "user" else "assistant",
                    "content": [{"type": "text", "text": m.content}]
                })
        return system_prompt, formatted

    async def generate(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1024,
        **kwargs
    ) -> LLMResponse:
        if not self.client:
            return LLMResponse(
                content="[Amazon Bedrock Provider: Please configure AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY.]",
                tool_calls=[],
                provider=self.provider_name,
                model=self.model_name
            )

        system_prompt, formatted_messages = self._convert_messages(messages)

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or 1024,
            "temperature": temperature,
            "messages": formatted_messages,
        }
        if system_prompt:
            body["system"] = system_prompt

        response = self.client.invoke_model(
            modelId=self.model_name,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )
        response_body = json.loads(response.get("body").read().decode("utf-8"))
        content = ""
        if "content" in response_body and len(response_body["content"]) > 0:
            content = response_body["content"][0].get("text", "")

        return LLMResponse(
            content=content,
            tool_calls=[],
            provider=self.provider_name,
            model=self.model_name,
            usage=response_body.get("usage", {})
        )

    async def stream(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1024,
        **kwargs
    ) -> AsyncIterator[str]:
        # Simple stream implementation using synchronous generation
        resp = await self.generate(messages, tools, temperature, max_tokens, **kwargs)
        yield resp.content


class BedrockEmbeddingProvider(BaseEmbeddingProvider):
    """Amazon Bedrock Titan / Cohere Embeddings provider."""

    def __init__(
        self,
        model_name: str = "amazon.titan-embed-text-v2:0",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
        **kwargs
    ):
        super().__init__(model_name=model_name, **kwargs)
        if BEDROCK_AVAILABLE and (aws_access_key_id or boto3.Session().get_credentials()):
            self.client = boto3.client(
                service_name="bedrock-runtime",
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
        else:
            self.client = None

    @property
    def provider_name(self) -> str:
        return "aws_bedrock"

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.client or not texts:
            return [[0.0] * 1024 for _ in texts]
        embeddings = []
        for text in texts:
            body = json.dumps({"inputText": text})
            response = self.client.invoke_model(
                modelId=self.model_name,
                contentType="application/json",
                accept="application/json",
                body=body
            )
            response_body = json.loads(response.get("body").read().decode("utf-8"))
            embeddings.append(response_body.get("embedding", []))
        return embeddings

    async def embed_query(self, text: str) -> List[float]:
        res = await self.embed_documents([text])
        return res[0]
