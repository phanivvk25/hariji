"""Data models for Multi-Project, Multi-Environment Self-Service Portal,
MCP Integration, HITL Governance, and Self-Service-Desk.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
import datetime


EnvironmentType = Literal["dev", "uat", "prod"]
SeverityType = Literal["P1", "P2", "P3"]
TicketStatus = Literal["open", "in_triage", "remediation_proposed", "resolved"]
ApprovalStatus = Literal["pending", "approved", "rejected"]


class PipelineNode(BaseModel):
    id: str
    name: str
    type: Literal["trigger", "orchestrator", "agent", "mcp_tool", "hitl_gate", "output"]
    config: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 100, "y": 100})


class PipelineEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None


class Pipeline(BaseModel):
    id: str
    project_id: str
    environment: EnvironmentType
    version: str = "1.0.0"
    is_readonly: bool = False
    name: str = "Main Orchestration Pipeline"
    nodes: List[PipelineNode] = Field(default_factory=list)
    edges: List[PipelineEdge] = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    promoted_from: Optional[str] = None


class Project(BaseModel):
    id: str
    name: str
    description: str
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    tags: List[str] = Field(default_factory=list)
    pipelines: Dict[EnvironmentType, Pipeline] = Field(default_factory=dict)


class PromotionRequest(BaseModel):
    source_env: EnvironmentType
    target_env: EnvironmentType
    version: str
    notes: str
    promoted_by: str = "Admin"


class PromotionRecord(BaseModel):
    id: str
    project_id: str
    from_env: EnvironmentType
    to_env: EnvironmentType
    version: str
    notes: str
    promoted_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    promoted_by: str
    status: str = "completed"


class MCPServerInfo(BaseModel):
    id: str
    name: str
    description: str
    transport: Literal["stdio", "sse", "http"] = "sse"
    endpoint: str
    status: Literal["connected", "disconnected", "error"] = "connected"
    tools_count: int = 0
    tools: List[Dict[str, Any]] = Field(default_factory=list)


class HITLPolicy(BaseModel):
    id: str
    project_id: str
    name: str = "Default HITL Policy"
    enabled: bool = True
    require_approval_for_blast_radius: Literal["low", "medium", "high"] = "medium"
    confidence_threshold: float = 0.85
    require_approval_for_promotion: bool = True
    require_approval_for_tools: List[str] = Field(
        default_factory=lambda: ["execute_db_mutation", "delete_cloud_resource", "issue_refund"]
    )
    auto_reject_timeout_minutes: int = 60


class HITLApprovalRequest(BaseModel):
    id: str
    project_id: str
    environment: EnvironmentType
    run_id: str
    step_name: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    risk_level: Literal["low", "medium", "high"] = "medium"
    status: ApprovalStatus = "pending"
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    decision_by: Optional[str] = None
    decision_reason: Optional[str] = None


class DeskTicket(BaseModel):
    id: str
    project_id: str
    environment: Literal["uat", "prod"]
    run_id: str
    title: str
    description: str
    error_type: str
    stack_trace: str
    severity: SeverityType = "P2"
    status: TicketStatus = "open"
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    resolved_at: Optional[str] = None
    triage_summary: Optional[str] = None
    proposed_remediation: Optional[Dict[str, Any]] = None
    auto_healed: Optional[bool] = False
    remediation_time_ms: Optional[int] = None
    itsm_sync: Optional[Dict[str, Any]] = None
    preventive_guardrail: Optional[str] = None


class DeskMetrics(BaseModel):
    total_incidents: int
    resolved_incidents: int
    auto_healed_count: int
    auto_healing_rate_pct: float
    avg_mttr_ms: float
    sla_compliance_pct: float
    active_open_count: int
    active_engine_status: str


class OrchestrationRunRequest(BaseModel):
    project_id: str
    environment: EnvironmentType
    query: str
    simulate_error: bool = False
    error_step: Optional[str] = None
