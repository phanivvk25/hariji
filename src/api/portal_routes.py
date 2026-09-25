"""FastAPI API routes for Self-Service Portal & Self-Service-Desk."""

import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.core.portal_models import (
    Project,
    Pipeline,
    PipelineNode,
    PipelineEdge,
    PromotionRequest,
    PromotionRecord,
    MCPServerInfo,
    HITLPolicy,
    HITLApprovalRequest,
    DeskTicket,
    DeskMetrics,
    OrchestrationRunRequest,
    EnvironmentType,
)
from src.services.portal_service import portal_service
from src.services.mcp_service import mcp_service
from src.services.hitl_service import hitl_service
from src.services.desk_service import desk_service
from src.agents.orchestrator_agent import core_orchestrator

router = APIRouter()


class CreateProjectRequest(BaseModel):
    name: str
    description: str
    tags: Optional[List[str]] = None


class UpdatePipelineRequest(BaseModel):
    nodes: List[PipelineNode]
    edges: List[PipelineEdge]
    version: Optional[str] = None


class ResolveApprovalRequest(BaseModel):
    approved: bool
    decision_by: str = "Admin Reviewer"
    reason: str = "Authorized by platform engineer."


class RegisterMCPServerRequest(BaseModel):
    name: str
    description: str
    transport: str = "sse"
    endpoint: str
    tools: Optional[List[Dict[str, Any]]] = None


# --- Project & Pipeline Management ---


@router.get("/projects", response_model=List[Project])
async def list_projects():
    """List all projects in the self-service portal."""
    return portal_service.list_projects()


@router.post("/projects", response_model=Project)
async def create_project(req: CreateProjectRequest):
    """Create a new isolated project with DEV, UAT, and PROD pipelines."""
    return portal_service.create_project(req.name, req.description, req.tags)


@router.get("/projects/{project_id}/pipelines/{env}", response_model=Pipeline)
async def get_pipeline(project_id: str, env: EnvironmentType):
    """Get the pipeline configuration for a specific project and environment."""
    return portal_service.get_pipeline(project_id, env)


@router.put("/projects/{project_id}/pipelines/{env}", response_model=Pipeline)
async def update_pipeline(project_id: str, env: EnvironmentType, req: UpdatePipelineRequest):
    """Update pipeline configuration. Strictly enforces DEV mutability; UAT/PROD are read-only."""
    return portal_service.update_dev_pipeline(
        project_id=project_id,
        environment=env,
        nodes=req.nodes,
        edges=req.edges,
        version=req.version,
    )


@router.post("/projects/{project_id}/promote", response_model=PromotionRecord)
async def promote_pipeline(project_id: str, req: PromotionRequest):
    """Promote a pipeline from DEV -> UAT or UAT -> PROD with immutable versioning."""
    return portal_service.promote_pipeline(project_id, req)


@router.get("/promotions", response_model=List[PromotionRecord])
async def get_promotion_history(project_id: Optional[str] = None):
    """List all promotion audit logs."""
    return portal_service.get_promotion_history(project_id)


# --- MCP Tool Registry ---


@router.get("/mcp/servers", response_model=List[MCPServerInfo])
async def list_mcp_servers():
    """List all connected Model Context Protocol servers and their discovered tools."""
    return mcp_service.list_servers()


@router.post("/mcp/servers", response_model=MCPServerInfo)
async def register_mcp_server(req: RegisterMCPServerRequest):
    """Register a new MCP server in the catalog."""
    return mcp_service.register_server(
        name=req.name,
        description=req.description,
        transport=req.transport,
        endpoint=req.endpoint,
        tools=req.tools,
    )


@router.get("/mcp/tools")
async def list_all_mcp_tools():
    """Get flat catalog of all tools exposed by connected MCP servers."""
    return {"tools": mcp_service.list_all_tools()}


# --- HITL Governance & Approvals ---


@router.get("/hitl/policy/{project_id}", response_model=HITLPolicy)
async def get_hitl_policy(project_id: str):
    """Get configurable HITL safety policy for a project."""
    return hitl_service.get_policy(project_id)


@router.put("/hitl/policy/{project_id}", response_model=HITLPolicy)
async def update_hitl_policy(project_id: str, policy: HITLPolicy):
    """Update HITL safety policies and risk thresholds for a project."""
    return hitl_service.update_policy(project_id, policy)


@router.get("/hitl/approvals", response_model=List[HITLApprovalRequest])
async def list_hitl_approvals(
    project_id: Optional[str] = None,
    environment: Optional[EnvironmentType] = None,
    status: Optional[str] = None,
):
    """List pending and resolved HITL approval requests."""
    return hitl_service.list_approvals(project_id, environment, status)


@router.post("/hitl/approvals/{approval_id}/resolve", response_model=HITLApprovalRequest)
async def resolve_hitl_approval(approval_id: str, req: ResolveApprovalRequest):
    """Approve or reject a pending HITL request."""
    try:
        return hitl_service.resolve_approval(
            approval_id=approval_id,
            approved=req.approved,
            decision_by=req.decision_by,
            reason=req.reason,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Self-Service-Desk (Incident & Healing Loop) ---


@router.get("/desk/tickets", response_model=List[DeskTicket])
async def list_desk_tickets(
    project_id: Optional[str] = None,
    environment: Optional[str] = None,
    status: Optional[str] = None,
):
    """List incident tickets logged in Self-Service-Desk from UAT and PROD."""
    return desk_service.list_tickets(project_id, environment, status)


@router.get("/desk/tickets/{ticket_id}", response_model=DeskTicket)
async def get_desk_ticket(ticket_id: str):
    """Get details of a specific incident ticket."""
    ticket = desk_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return ticket


@router.post("/desk/tickets/{ticket_id}/triage", response_model=DeskTicket)
async def triage_ticket(ticket_id: str):
    """Trigger the Autonomous Triage Agent to re-evaluate RCA and propose remediation."""
    try:
        return desk_service.triage_ticket(ticket_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/desk/tickets/{ticket_id}/apply-remediation", response_model=DeskTicket)
async def apply_desk_remediation(ticket_id: str):
    """Apply the Autonomous Agent's proposed remediation directly to the DEV pipeline!"""
    try:
        return desk_service.apply_remediation_to_dev(ticket_id)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/desk/tickets/{ticket_id}/auto-heal", response_model=DeskTicket)
async def auto_heal_ticket(ticket_id: str):
    """Executes full zero-touch autonomous healing: triage, apply patch to DEV, record MTTR, sync ITSM."""
    try:
        return desk_service.auto_heal_ticket(ticket_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/desk/auto-heal-all")
async def auto_heal_all_tickets(project_id: Optional[str] = None):
    """Autonomously resolves all unresolved incidents across the fleet in batch."""
    return desk_service.auto_heal_all(project_id)


class SimulateAnomalyRequest(BaseModel):
    project_id: str
    environment: Optional[str] = "uat"
    anomaly_type: Optional[str] = None


@router.post("/desk/simulate-telemetry-anomaly", response_model=DeskTicket)
async def simulate_telemetry_anomaly(req: SimulateAnomalyRequest):
    """Simulates an incoming live runtime anomaly from UAT or PROD."""
    return desk_service.simulate_telemetry_anomaly(
        project_id=req.project_id,
        environment=req.environment or "uat",
        anomaly_type=req.anomaly_type
    )


@router.get("/desk/metrics", response_model=DeskMetrics)
async def get_desk_metrics(project_id: Optional[str] = None):
    """Returns aggregated real-time metrics on autonomous healing rate, MTTR, and SLA."""
    return desk_service.get_metrics(project_id)


# --- Orchestration Execution Loop ---


@router.post("/orchestrate")
async def run_orchestration(req: OrchestrationRunRequest):
    """Run Core Orchestrator Agent with cognitive thinking, decision making,
    MCP tool execution, HITL checking, and automated UAT/PROD error ticketing.
    """

    async def event_generator():
        async for step in core_orchestrator.run(
            query=req.query,
            project_id=req.project_id,
            environment=req.environment,
            simulate_error=req.simulate_error,
            error_step=req.error_step,
        ):
            yield f"data: {json.dumps(step.model_dump())}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
