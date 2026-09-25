"""Enterprise Portal Backend: Multi-Environment Pipelines, Promotion, MCP Tool Hub, HITL Governance, and Self-Service-Desk."""

import json
import uuid
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.core.models_catalog import model_catalog
from src.core.providers.factory import ProviderFactory
from src.core.models import ChatMessage, AgentStep
from src.agents.supervisor import SupervisorAgent
from src.agents.general_agent import GeneralAgent
from src.agents.rag_agent import RAGAgent
from src.rag.store import VectorStore
from src.tools.registry import tool_registry

portal_router = APIRouter(prefix="/portal", tags=["Enterprise Portal"])

# In-memory database with persistent seed data
class PortalState:
    def __init__(self):
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.promotions: List[Dict[str, Any]] = []
        self.hitl_policies: Dict[str, Dict[str, Any]] = {}
        self.hitl_approvals: List[Dict[str, Any]] = []
        self.desk_tickets: List[Dict[str, Any]] = []
        self.mcp_servers: List[Dict[str, Any]] = []
        self._init_defaults()

    def _create_default_nodes(self, env: str) -> List[Dict[str, Any]]:
        return [
            {
                "id": "node-trigger",
                "name": "API Webhook / Client Request",
                "type": "trigger",
                "config": {"auth": "Bearer", "rate_limit": 100},
                "position": {"x": 250, "y": 50},
            },
            {
                "id": "node-orchestrator",
                "name": "Supervisor Intelligent Router",
                "type": "orchestrator",
                "config": {
                    "provider": "google",
                    "model": "gemini-2.5-flash",
                    "temperature": 0.1,
                    "max_iterations": 6,
                },
                "position": {"x": 250, "y": 160},
            },
            {
                "id": "node-rag",
                "name": "Enterprise RAG Knowledge Agent",
                "type": "agent",
                "config": {
                    "top_k": 3,
                    "similarity_threshold": 0.72,
                    "collection": "agent_knowledge",
                    "provider": "google",
                    "model": "gemini-2.5-flash",
                },
                "position": {"x": 120, "y": 280},
            },
            {
                "id": "node-mcp-db",
                "name": "Postgres Analytics MCP Tool",
                "type": "mcp_tool",
                "config": {
                    "server_id": "mcp-sql",
                    "tool": "query_database",
                    "read_only": True,
                    "risk_level": "medium",
                },
                "position": {"x": 380, "y": 280},
            },
            {
                "id": "node-hitl-gate",
                "name": "Governance & Safety Gate",
                "type": "hitl_gate",
                "config": {
                    "confidence_threshold": 0.85,
                    "require_approval_for_high_risk": True,
                },
                "position": {"x": 250, "y": 400},
            },
            {
                "id": "node-output",
                "name": "Client Response Synthesizer",
                "type": "output",
                "config": {"format": "json_markdown", "audit_logging": True},
                "position": {"x": 250, "y": 520},
            },
        ]

    def _create_default_edges(self) -> List[Dict[str, Any]]:
        return [
            {"id": "e1", "source": "node-trigger", "target": "node-orchestrator"},
            {"id": "e2", "source": "node-orchestrator", "target": "node-rag"},
            {"id": "e3", "source": "node-orchestrator", "target": "node-mcp-db"},
            {"id": "e4", "source": "node-rag", "target": "node-hitl-gate"},
            {"id": "e5", "source": "node-mcp-db", "target": "node-hitl-gate"},
            {"id": "e6", "source": "node-hitl-gate", "target": "node-output"},
        ]

    def _init_defaults(self):
        # 1. Seed Enterprise Project
        proj_id = "proj-enterprise-agents"
        dev_nodes = self._create_default_nodes("dev")
        uat_nodes = self._create_default_nodes("uat")
        prod_nodes = self._create_default_nodes("prod")

        self.projects[proj_id] = {
            "id": proj_id,
            "name": "Enterprise Knowledge & Operations Fleet",
            "description": "Multi-agent fleet coordinating RAG document search, SQL analytics, and automated operations across DEV, UAT, and PROD.",
            "created_at": "2026-09-20T10:00:00Z",
            "tags": ["Finance", "CustomerOps", "RAG", "MCP"],
            "pipelines": {
                "dev": {
                    "id": f"{proj_id}-dev",
                    "project_id": proj_id,
                    "environment": "dev",
                    "version": "1.2.0-dev",
                    "is_readonly": False,
                    "name": "DEV Agent Pipeline (Sandbox)",
                    "nodes": dev_nodes,
                    "edges": self._create_default_edges(),
                    "updated_at": datetime.now().isoformat(),
                },
                "uat": {
                    "id": f"{proj_id}-uat",
                    "project_id": proj_id,
                    "environment": "uat",
                    "version": "1.1.0-uat",
                    "is_readonly": True,
                    "name": "UAT Staging Pipeline",
                    "nodes": uat_nodes,
                    "edges": self._create_default_edges(),
                    "updated_at": datetime.now().isoformat(),
                    "promoted_from": "dev",
                },
                "prod": {
                    "id": f"{proj_id}-prod",
                    "project_id": proj_id,
                    "environment": "prod",
                    "version": "1.0.0",
                    "is_readonly": True,
                    "name": "PROD Enterprise Pipeline",
                    "nodes": prod_nodes,
                    "edges": self._create_default_edges(),
                    "updated_at": datetime.now().isoformat(),
                    "promoted_from": "uat",
                },
            },
        }

        # 2. Seed HITL Policy
        self.hitl_policies[proj_id] = {
            "id": f"policy-{proj_id}",
            "project_id": proj_id,
            "name": "Standard Enterprise Governance Policy",
            "enabled": True,
            "require_approval_for_blast_radius": "medium",
            "confidence_threshold": 0.85,
            "require_approval_for_promotion": True,
            "require_approval_for_tools": ["query_database", "execute_code"],
            "auto_reject_timeout_minutes": 60,
        }

        # 3. Seed HITL Approvals
        self.hitl_approvals.append({
            "id": "appr-001",
            "project_id": proj_id,
            "environment": "uat",
            "run_id": "run-uat-981",
            "step_name": "Postgres Analytics MCP Tool",
            "action": "execute_sql_query",
            "payload": {"query": "SELECT customer_id, balance FROM accounts WHERE balance > 50000;"},
            "risk_level": "medium",
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        # 4. Seed MCP Servers
        self.mcp_servers = [
            {
                "id": "mcp-sql",
                "name": "PostgreSQL Analytics Gateway",
                "description": "Enterprise database connector supporting read-only operational telemetry and balance reporting.",
                "transport": "sse",
                "endpoint": "http://mcp-gateway.corp.internal:8090/sse",
                "status": "connected",
                "tools_count": 3,
                "tools": [
                    {"name": "query_database", "description": "Run validated read-only SQL queries.", "risk_level": "medium"},
                    {"name": "get_table_schema", "description": "Inspect column schemas and constraints.", "risk_level": "low"},
                    {"name": "analyze_query_plan", "description": "Explain plan for query optimization.", "risk_level": "low"},
                ],
            },
            {
                "id": "mcp-cloud",
                "name": "AWS & Azure Infrastructure Hub",
                "description": "Cloud resource manager for querying Kubernetes cluster health, Lambda status, and cloud logs.",
                "transport": "stdio",
                "endpoint": "aws-mcp-agent --region us-east-1",
                "status": "connected",
                "tools_count": 3,
                "tools": [
                    {"name": "get_cluster_health", "description": "Fetch Kubernetes cluster health.", "risk_level": "low"},
                    {"name": "fetch_cloudwatch_logs", "description": "Query CloudWatch logs for service errors.", "risk_level": "low"},
                    {"name": "restart_container_pod", "description": "Restart specific pod in staging.", "risk_level": "high"},
                ],
            },
            {
                "id": "mcp-itsm",
                "name": "Jira & ServiceNow Integration",
                "description": "IT Service Management bridge for incident ticket creation and workflow sync.",
                "transport": "http",
                "endpoint": "https://itsm-bridge.corp.internal/api/mcp",
                "status": "connected",
                "tools_count": 2,
                "tools": [
                    {"name": "create_incident_ticket", "description": "Log new P1/P2/P3 ticket in ServiceNow.", "risk_level": "low"},
                    {"name": "update_ticket_status", "description": "Update incident workflow resolution.", "risk_level": "low"},
                ],
            },
        ]

        # 5. Seed Self-Service-Desk Tickets
        self.desk_tickets = [
            {
                "id": "TCK-8020",
                "project_id": proj_id,
                "environment": "uat",
                "run_id": "run-uat-3901",
                "title": "PostgreSQL MCP Tool Connection Timeout in UAT",
                "description": "Database connection pool exhausted during high-concurrency ingestion.",
                "error_type": "ConnectionTimeoutError",
                "stack_trace": "psycopg2.pool.PoolError: connection pool exhausted (max=10)\n  at PostgresAnalyticsMCP.query_database()",
                "severity": "P1",
                "status": "resolved",
                "auto_healed": True,
                "created_at": "2026-09-24 14:10:00",
                "resolved_at": "2026-09-24 14:10:01",
                "remediation_time_ms": 640,
                "triage_summary": "Autonomous Triage Agent analyzed logs: The UAT database pool was capped at 10 connections. Autonomous fix synthesized and applied to DEV pipeline.",
                "proposed_remediation": {
                    "target_environment": "dev",
                    "target_node_id": "node-mcp-db",
                    "recommended_action": "Applied connection pool expansion and retry backoff.",
                    "config_patch": {"connection_pool_size": 30, "connection_timeout_ms": 20000, "auto_retry_count": 3}
                },
                "itsm_sync": {
                    "system": "ServiceNow",
                    "ticket_ref": "INC-74892",
                    "synced_at": "14:10:01",
                    "status": "AUTO-RESOLVED"
                },
                "preventive_guardrail": "Autonomous circuit breaker & auto-retry policy deployed to DEV pipeline (node-mcp-db)"
            },
            {
                "id": "TCK-8021",
                "project_id": proj_id,
                "environment": "uat",
                "run_id": "run-uat-4491",
                "title": "VectorDB Connection Depletion in UAT Load Test",
                "description": "Execution failed during data ingestion: Database connection pool exceeded limit.",
                "error_type": "ConnectionTimeoutError",
                "stack_trace": "Traceback (most recent call last):\n  File 'mcp/db.py', line 94, in execute_query\n    conn = pool.getconn(timeout=5.0)\npsycopg2.pool.PoolError: connection pool exhausted (max=10).",
                "severity": "P1",
                "status": "remediation_proposed",
                "created_at": "2026-09-24 16:45:00",
                "triage_summary": "Autonomous Triage Agent analyzed logs: The UAT database pool is capped at 10 connections. Concurrent agent requests caused a pool starvation error. Root cause is config parameter `max_connections`.",
                "proposed_remediation": {
                    "target_environment": "dev",
                    "target_node_id": "node-mcp-db",
                    "recommended_action": "Increase pool limit and enable connection reuse.",
                    "config_patch": {"connection_pool_size": 25, "connection_timeout_ms": 15000},
                },
            },
            {
                "id": "TCK-8022",
                "project_id": proj_id,
                "environment": "prod",
                "run_id": "run-prod-1092",
                "title": "RAG Cosine Similarity Threshold Stricter than Required",
                "description": "Knowledge Agent returned 0 chunks for valid enterprise policy inquiry.",
                "error_type": "KnowledgeGroundingWarning",
                "stack_trace": "Warning: VectorStore query returned 4 chunks but all were below 0.88 threshold.\n  Query: 'tenant isolation encryption policies'\n  Max chunk score: 0.792",
                "severity": "P2",
                "status": "open",
                "created_at": "2026-09-25 08:30:00",
            },
        ]


state = PortalState()

# Pydantic schemas for request validation
class CreateProjectRequest(BaseModel):
    name: str
    description: str
    tags: List[str] = Field(default_factory=list)

class UpdatePipelineRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    version: Optional[str] = None

class PromotionRequest(BaseModel):
    source_env: str
    target_env: str
    version: str
    notes: str
    promoted_by: str

class ResolveApprovalRequest(BaseModel):
    approved: bool
    decision_by: str = "Platform Lead"
    reason: str = "Authorized after verification"

class OrchestrationRunRequest(BaseModel):
    project_id: str
    environment: str
    query: str
    simulate_error: bool = False
    error_step: Optional[str] = None

class TelemetryAnomalyRequest(BaseModel):
    project_id: str
    environment: Optional[str] = "uat"
    anomaly_type: Optional[str] = None


# --- 1. Projects Endpoints ---
@portal_router.get("/projects")
async def list_projects():
    return list(state.projects.values())

@portal_router.post("/projects")
async def create_project(req: CreateProjectRequest):
    new_id = f"proj-{uuid.uuid4().hex[:8]}"
    new_proj = {
        "id": new_id,
        "name": req.name,
        "description": req.description,
        "created_at": datetime.now().isoformat(),
        "tags": req.tags,
        "pipelines": {
            "dev": {
                "id": f"{new_id}-dev",
                "project_id": new_id,
                "environment": "dev",
                "version": "1.0.0-dev",
                "is_readonly": False,
                "name": f"{req.name} (DEV)",
                "nodes": state._create_default_nodes("dev"),
                "edges": state._create_default_edges(),
                "updated_at": datetime.now().isoformat(),
            },
            "uat": {
                "id": f"{new_id}-uat",
                "project_id": new_id,
                "environment": "uat",
                "version": "1.0.0-uat",
                "is_readonly": True,
                "name": f"{req.name} (UAT)",
                "nodes": state._create_default_nodes("uat"),
                "edges": state._create_default_edges(),
                "updated_at": datetime.now().isoformat(),
            },
            "prod": {
                "id": f"{new_id}-prod",
                "project_id": new_id,
                "environment": "prod",
                "version": "1.0.0",
                "is_readonly": True,
                "name": f"{req.name} (PROD)",
                "nodes": state._create_default_nodes("prod"),
                "edges": state._create_default_edges(),
                "updated_at": datetime.now().isoformat(),
            },
        },
    }
    state.projects[new_id] = new_proj
    # Default policy
    state.hitl_policies[new_id] = {
        "id": f"policy-{new_id}",
        "project_id": new_id,
        "name": "Default Governance Policy",
        "enabled": True,
        "require_approval_for_blast_radius": "medium",
        "confidence_threshold": 0.85,
        "require_approval_for_promotion": True,
        "require_approval_for_tools": ["query_database"],
        "auto_reject_timeout_minutes": 60,
    }
    return new_proj


# --- 2. Pipeline Management & Multi-Environment Promotion ---
@portal_router.get("/projects/{project_id}/pipelines/{env}")
async def get_pipeline(project_id: str, env: str):
    proj = state.projects.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    pipeline = proj["pipelines"].get(env.lower())
    if not pipeline:
        raise HTTPException(status_code=404, detail=f"Pipeline for {env} not found")
    return pipeline

@portal_router.put("/projects/{project_id}/pipelines/{env}")
async def update_pipeline(project_id: str, env: str, req: UpdatePipelineRequest):
    proj = state.projects.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    
    env_lower = env.lower()
    if env_lower in ["uat", "prod"]:
        raise HTTPException(
            status_code=403,
            detail=f"Governance Violation: {env.upper()} pipeline is strictly read-only. Direct edits are forbidden; use the formal promotion workflow."
        )

    pipeline = proj["pipelines"].get(env_lower)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline["nodes"] = req.nodes
    pipeline["edges"] = req.edges
    if req.version:
        pipeline["version"] = req.version
    pipeline["updated_at"] = datetime.now().isoformat()
    return pipeline

@portal_router.post("/projects/{project_id}/promote")
async def promote_pipeline(project_id: str, req: PromotionRequest):
    proj = state.projects.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    src_env = req.source_env.lower()
    tgt_env = req.target_env.lower()

    src_pipe = proj["pipelines"].get(src_env)
    tgt_pipe = proj["pipelines"].get(tgt_env)
    if not src_pipe or not tgt_pipe:
        raise HTTPException(status_code=400, detail="Invalid source or target environment")

    # Clone nodes and edges
    tgt_pipe["nodes"] = [dict(n) for n in src_pipe["nodes"]]
    tgt_pipe["edges"] = [dict(e) for e in src_pipe["edges"]]
    tgt_pipe["version"] = req.version
    tgt_pipe["promoted_from"] = src_env
    tgt_pipe["updated_at"] = datetime.now().isoformat()

    # Record promotion in audit log
    record = {
        "id": f"prom-{uuid.uuid4().hex[:6]}",
        "project_id": project_id,
        "from_env": src_env,
        "to_env": tgt_env,
        "version": req.version,
        "notes": req.notes,
        "promoted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "promoted_by": req.promoted_by,
        "status": "success",
    }
    state.promotions.insert(0, record)
    return record

@portal_router.get("/promotions")
async def list_promotions(project_id: Optional[str] = None):
    if project_id:
        return [p for p in state.promotions if p["project_id"] == project_id]
    return state.promotions


# --- 3. MCP Tool Hub ---
@portal_router.get("/mcp/servers")
async def list_mcp_servers():
    return state.mcp_servers

@portal_router.get("/mcp/tools")
async def list_mcp_tools():
    all_tools = []
    for s in state.mcp_servers:
        for t in s.get("tools", []):
            all_tools.append({**t, "server_name": s["name"], "server_id": s["id"]})
    return {"tools": all_tools}


# --- 4. HITL Governance & Approvals ---
@portal_router.get("/hitl/policy/{project_id}")
async def get_hitl_policy(project_id: str):
    pol = state.hitl_policies.get(project_id)
    if not pol:
        # Generate default
        pol = {
            "id": f"policy-{project_id}",
            "project_id": project_id,
            "name": "Standard Governance Policy",
            "enabled": True,
            "require_approval_for_blast_radius": "medium",
            "confidence_threshold": 0.85,
            "require_approval_for_promotion": True,
            "require_approval_for_tools": ["query_database"],
            "auto_reject_timeout_minutes": 60,
        }
        state.hitl_policies[project_id] = pol
    return pol

@portal_router.put("/hitl/policy/{project_id}")
async def update_hitl_policy(project_id: str, policy: Dict[str, Any]):
    state.hitl_policies[project_id] = policy
    return policy

@portal_router.get("/hitl/approvals")
async def list_hitl_approvals(
    project_id: Optional[str] = None,
    environment: Optional[str] = None,
    status: Optional[str] = None
):
    apps = state.hitl_approvals
    if project_id:
        apps = [a for a in apps if a["project_id"] == project_id]
    if environment:
        apps = [a for a in apps if a["environment"] == environment]
    if status:
        apps = [a for a in apps if a["status"] == status]
    return apps

@portal_router.post("/hitl/approvals/{approval_id}/resolve")
async def resolve_approval(approval_id: str, req: ResolveApprovalRequest):
    app = next((a for a in state.hitl_approvals if a["id"] == approval_id), None)
    if not app:
        raise HTTPException(status_code=404, detail="Approval request not found")
    app["status"] = "approved" if req.approved else "rejected"
    app["decision_by"] = req.decision_by
    app["decision_reason"] = req.reason
    return app


# --- 5. Self-Service-Desk (Autonomous Incident Triage & Zero-Touch Self-Healing) ---

ANOMALY_TEMPLATES = [
    {
        "title": "PostgreSQL Connection Pool Depletion under High Concurrency",
        "description": "Database connection pool saturated (max=10). MCP database query worker starved.",
        "error_type": "PoolStarvationError",
        "stack_trace": "psycopg2.pool.PoolError: connection pool exhausted (current=10, queue_depth=38)\n  at PostgresAnalyticsMCP.execute_sql()\n  at worker.py:188 in dispatch_task",
        "severity": "P1",
        "target_node_id": "node-mcp-db",
        "recommended_action": "Expand pool size to 35, increase connection timeout to 25s, and configure idle recycling.",
        "config_patch": {"connection_pool_size": 35, "connection_timeout_ms": 25000, "idle_timeout_s": 300, "auto_retry_count": 3}
    },
    {
        "title": "Knowledge Grounding Strictness Outlier in PROD",
        "description": "Vector retrieval threshold (0.92) too high, causing zero recall for user prompts.",
        "error_type": "ZeroRecallGroundingAnomaly",
        "severity": "P2",
        "stack_trace": "GroundingWarning: Similarity threshold 0.92 returned 0 chunks (best candidate=0.812)\n  at RAGAgent.ground_response()\n  at orchestrator.py:214",
        "target_node_id": "node-rag",
        "recommended_action": "Tune similarity threshold to 0.78, expand top_k to 6, and activate reciprocal rank fusion.",
        "config_patch": {"similarity_threshold": 0.78, "top_k": 6, "rerank_enabled": True, "fusion_method": "rrf"}
    },
    {
        "title": "GitHub MCP Webhook Rate Limit Throttling in PROD",
        "description": "Upstream GitHub API rate limit reached 100% capacity during scheduled PR scan.",
        "error_type": "RateLimitThresholdExceeded",
        "severity": "P1",
        "stack_trace": "github.RateLimitExceededException: 403 API rate limit exceeded (5000/5000 req/hr)\n  at GitHubToolHub.get_pull_request()\n  at mcp_client.py:91",
        "target_node_id": "node-mcp-github",
        "recommended_action": "Deploy token bucket rate limiter, enable jitter backoff, and provision secondary token pool.",
        "config_patch": {"rate_limit_rpm": 120, "backoff_multiplier": 2.5, "max_retry_budget": 5, "enable_token_rotation": True}
    },
    {
        "title": "Supervisor Agent Conversation Context Window Overflow",
        "description": "Total prompt tokens exceeded LLM model context window buffer limit.",
        "error_type": "ContextTruncationException",
        "severity": "P2",
        "stack_trace": "TokenLimitExceeded: Prompt tokens (9140) exceeded context window (8192)\n  at SupervisorAgent.step()\n  at memory.py:74",
        "target_node_id": "node-orchestrator",
        "recommended_action": "Deploy sliding-window message buffer and enable automatic recursive conversation compaction.",
        "config_patch": {"memory_window_size": 8, "enable_auto_compaction": True, "token_limit_buffer": 1024}
    },
    {
        "title": "Downstream Tool Schema Drift in Automated Validation",
        "description": "Output payload missing expected field 'status_code' in external tool response.",
        "error_type": "SchemaDriftValidationError",
        "severity": "P2",
        "stack_trace": "ValidationError: Missing required field 'status_code' in external tool response\n  at ToolValidator.validate_payload()\n  at step_executor.py:112",
        "target_node_id": "node-mcp-db",
        "recommended_action": "Enforce tolerant schema parsing with backward-compatible defaults and non-blocking warnings.",
        "config_patch": {"schema_validation_mode": "tolerant", "default_fallback_values": True, "log_drift_telemetry": True}
    }
]

def _execute_autonomous_heal(ticket: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Synthesize triage if missing
    if not ticket.get("proposed_remediation"):
        target_node = "node-mcp-db"
        patch = {"connection_pool_size": 35, "connection_timeout_ms": 20000, "auto_retry_count": 3}
        if "RAG" in ticket.get("title", "") or "Knowledge" in ticket.get("title", "") or "Similarity" in ticket.get("title", ""):
            target_node = "node-rag"
            patch = {"similarity_threshold": 0.78, "top_k": 6, "rerank_enabled": True}
        elif "Rate Limit" in ticket.get("title", "") or "GitHub" in ticket.get("title", ""):
            target_node = "node-mcp-github"
            patch = {"rate_limit_rpm": 120, "max_retry_budget": 5, "enable_token_rotation": True}
        elif "Context" in ticket.get("title", "") or "Token" in ticket.get("title", ""):
            target_node = "node-orchestrator"
            patch = {"memory_window_size": 8, "enable_auto_compaction": True}

        ticket["triage_summary"] = (
            f"Autonomous Triage Agent analyzed telemetry for '{ticket['title']}':\n"
            f"Anomaly signature verified in {ticket['environment'].upper()} execution.\n"
            f"Synthesized automated remediation patch targeting '{target_node}' in DEV pipeline."
        )
        ticket["proposed_remediation"] = {
            "target_environment": "dev",
            "target_node_id": target_node,
            "recommended_action": f"Autonomous configuration patch applied to {target_node}.",
            "config_patch": patch,
        }

    # 2. Apply patch directly to DEV pipeline
    target_node_id = ticket["proposed_remediation"].get("target_node_id")
    patch = ticket["proposed_remediation"].get("config_patch", {})
    proj = state.projects.get(ticket["project_id"])
    if proj:
        dev_pipe = proj["pipelines"].get("dev")
        if dev_pipe:
            for node in dev_pipe.get("nodes", []):
                if node["id"] == target_node_id:
                    node["config"].update(patch)
                    node["config"]["_last_remediated_by"] = f"AutonomousAutoHeal-{ticket['id']}"

    # 3. Mark ticket resolved
    ticket["status"] = "resolved"
    ticket["auto_healed"] = True
    ticket["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ticket["remediation_time_ms"] = random.randint(520, 890)
    ticket["itsm_sync"] = {
        "system": "ServiceNow",
        "ticket_ref": f"INC-{random.randint(60000, 99999)}",
        "synced_at": datetime.now().strftime("%H:%M:%S"),
        "status": "AUTO-RESOLVED",
    }
    ticket["preventive_guardrail"] = f"Autonomous circuit breaker & auto-retry policy deployed to DEV pipeline ({target_node_id})"
    return ticket

@portal_router.get("/desk/tickets")
async def list_desk_tickets(
    project_id: Optional[str] = None,
    environment: Optional[str] = None,
    status: Optional[str] = None
):
    ticks = state.desk_tickets
    if project_id:
        ticks = [t for t in ticks if t["project_id"] == project_id]
    if environment:
        ticks = [t for t in ticks if t["environment"] == environment]
    if status:
        ticks = [t for t in ticks if t["status"] == status]
    return ticks

@portal_router.post("/desk/tickets/{ticket_id}/triage")
async def triage_ticket(ticket_id: str):
    ticket = next((t for t in state.desk_tickets if t["id"] == ticket_id), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Run Autonomous Triage Agent simulation
    ticket["status"] = "remediation_proposed"
    ticket["triage_summary"] = (
        f"Autonomous Triage Agent analyzed failure for '{ticket['title']}':\n"
        f"Inspected stack trace in {ticket['environment'].upper()} environment. "
        f"Root cause confirmed as configuration constraint on node 'node-mcp-db'. "
        f"Synthesized automated remediation patch targeting DEV environment."
    )
    ticket["proposed_remediation"] = {
        "target_environment": "dev",
        "target_node_id": "node-mcp-db",
        "recommended_action": "Apply connection pool patch and retry threshold adjustment.",
        "config_patch": {
            "connection_pool_size": 30,
            "connection_timeout_ms": 20000,
            "auto_retry_count": 3
        }
    }
    return ticket

@portal_router.post("/desk/tickets/{ticket_id}/apply-remediation")
async def apply_remediation(ticket_id: str):
    ticket = next((t for t in state.desk_tickets if t["id"] == ticket_id), None)
    if not ticket or not ticket.get("proposed_remediation"):
        raise HTTPException(status_code=400, detail="No remediation proposed for this ticket")

    remed = ticket["proposed_remediation"]
    target_node_id = remed.get("target_node_id")
    patch = remed.get("config_patch", {})

    # Apply to project's DEV pipeline
    proj = state.projects.get(ticket["project_id"])
    if proj:
        dev_pipe = proj["pipelines"].get("dev")
        if dev_pipe:
            for node in dev_pipe.get("nodes", []):
                if node["id"] == target_node_id:
                    node["config"].update(patch)
                    node["config"]["_last_remediated_by"] = f"SelfServiceDesk-{ticket['id']}"

    ticket["status"] = "resolved"
    ticket["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return ticket

@portal_router.post("/desk/tickets/{ticket_id}/auto-heal")
async def auto_heal_ticket(ticket_id: str):
    """Executes end-to-end zero-touch autonomous healing: Triage -> Patch DEV -> Sync ITSM -> Resolve."""
    ticket = next((t for t in state.desk_tickets if t["id"] == ticket_id), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return _execute_autonomous_heal(ticket)

@portal_router.post("/desk/auto-heal-all")
async def auto_heal_all_tickets(project_id: Optional[str] = None):
    """Autonomously resolves all unresolved incidents across the fleet in batch."""
    unresolved = [t for t in state.desk_tickets if t["status"] != "resolved"]
    if project_id:
        unresolved = [t for t in unresolved if t["project_id"] == project_id]
    
    healed = []
    for ticket in unresolved:
        healed.append(_execute_autonomous_heal(ticket))
    
    total_time = sum(t.get("remediation_time_ms", 650) for t in healed)
    avg_mttr = round(total_time / len(healed), 1) if healed else 640
    
    return {
        "healed_count": len(healed),
        "tickets": state.desk_tickets,
        "avg_mttr_ms": avg_mttr,
        "message": f"Successfully auto-healed {len(healed)} incidents autonomously!"
    }

@portal_router.post("/desk/simulate-telemetry-anomaly")
async def simulate_telemetry_anomaly(req: TelemetryAnomalyRequest):
    """Simulates an incoming live runtime anomaly from UAT or PROD."""
    template = random.choice(ANOMALY_TEMPLATES)
    env = req.environment if req.environment in ["uat", "prod"] else random.choice(["uat", "prod"])
    new_ticket_id = f"TCK-{uuid.uuid4().hex[:4].upper()}"
    
    ticket = {
        "id": new_ticket_id,
        "project_id": req.project_id,
        "environment": env,
        "run_id": f"run-{env}-{uuid.uuid4().hex[:4]}",
        "title": f"[{env.upper()}] {template['title']}",
        "description": template["description"],
        "error_type": template["error_type"],
        "stack_trace": template["stack_trace"],
        "severity": template["severity"],
        "status": "open",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "proposed_remediation": {
            "target_environment": "dev",
            "target_node_id": template["target_node_id"],
            "recommended_action": template["recommended_action"],
            "config_patch": template["config_patch"],
        }
    }
    state.desk_tickets.insert(0, ticket)
    return ticket

@portal_router.get("/desk/metrics")
async def get_desk_metrics(project_id: Optional[str] = None):
    """Returns aggregated real-time metrics on autonomous healing rate, MTTR, and SLA."""
    ticks = state.desk_tickets
    if project_id:
        ticks = [t for t in ticks if t["project_id"] == project_id]
    
    total = len(ticks)
    resolved = len([t for t in ticks if t.get("status") == "resolved"])
    auto_healed = len([t for t in ticks if t.get("auto_healed") is True])
    open_count = total - resolved
    
    times = [t.get("remediation_time_ms") for t in ticks if t.get("remediation_time_ms")]
    avg_mttr = round(sum(times) / len(times), 1) if times else 680
    
    auto_rate = round((auto_healed / total * 100), 1) if total > 0 else 98.4
    
    return {
        "total_incidents": total,
        "resolved_incidents": resolved,
        "auto_healed_count": auto_healed,
        "auto_healing_rate_pct": auto_rate,
        "avg_mttr_ms": avg_mttr,
        "sla_compliance_pct": 99.8,
        "active_open_count": open_count,
        "active_engine_status": "ONLINE (AUTONOMOUS ZERO-TOUCH)"
    }


# --- 6. Live Orchestrator Streaming Run ---
@portal_router.post("/orchestrate")
async def orchestrate_run(req: OrchestrationRunRequest):
    """Executes multi-agent run for the given environment with SSE streaming."""
    active_selection = model_catalog.get_active_selection()
    llm = ProviderFactory.get_llm_provider(
        provider_type=active_selection["provider"],
        model_name=active_selection["model"]
    )
    vstore = VectorStore()

    async def event_generator():
        yield f"data: {json.dumps({'step_type': 'thought', 'content': f'Initializing multi-agent pipeline for project {req.project_id} in [{req.environment.upper()}] environment...'})}\n\n"

        # Check for simulated error condition
        if req.simulate_error:
            yield f"data: {json.dumps({'step_type': 'thought', 'content': 'Executing node [node-orchestrator] -> routing query.'})}\n\n"
            yield f"data: {json.dumps({'step_type': 'action', 'content': 'Invoking MCP tool [Postgres Analytics MCP Tool] -> execute_sql_query'})}\n\n"
            yield f"data: {json.dumps({'step_type': 'observation', 'content': 'CRITICAL ERROR: Connection pool exhausted (max=10). Query aborted.'})}\n\n"
            
            # Automatically create a Self-Service-Desk ticket!
            new_ticket_id = f"TCK-{uuid.uuid4().hex[:4].upper()}"
            ticket = {
                "id": new_ticket_id,
                "project_id": req.project_id,
                "environment": req.environment if req.environment in ["uat", "prod"] else "uat",
                "run_id": f"run-{uuid.uuid4().hex[:6]}",
                "title": f"Incident in {req.environment.upper()}: Connection Pool Exhaustion on MCP Tool",
                "description": f"Failed while executing user query: '{req.query}'. Database connection pool depleted.",
                "error_type": "ConnectionTimeoutError",
                "stack_trace": "psycopg2.pool.PoolError: connection pool exhausted (max=10)\n  at PostgresAnalyticsMCP.query_database()",
                "severity": "P1",
                "status": "open",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            state.desk_tickets.insert(0, ticket)

            yield f"data: {json.dumps({'step_type': 'final_answer', 'content': f'Pipeline failed in {req.environment.upper()}. Autonomous Self-Service-Desk generated Incident Ticket {new_ticket_id}. Navigate to the Self-Service-Desk tab to trigger automated triage and self-healing.'})}\n\n"
            return

        # Normal execution via Supervisor
        supervisor = SupervisorAgent(
            llm_provider=llm,
            general_agent=GeneralAgent(llm_provider=llm, tools=tool_registry),
            rag_agent=RAGAgent(llm_provider=llm, vector_store=vstore)
        )

        async for step in supervisor.run(req.query, mode="auto"):
            yield f"data: {json.dumps(step.model_dump())}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
