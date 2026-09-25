"""Common data models and contracts for messages, tools, responses, and agent steps."""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class ToolParameter(BaseModel):
    type: str
    description: str
    enum: Optional[List[str]] = None
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class LLMResponse(BaseModel):
    content: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    provider: str
    model: str
    usage: Dict[str, int] = Field(default_factory=dict)
    finish_reason: Optional[str] = None


class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None
    source: Optional[str] = None
    page: Optional[int] = None


class AgentStep(BaseModel):
    step_type: Literal["thought", "action", "observation", "citation", "final_answer"]
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
