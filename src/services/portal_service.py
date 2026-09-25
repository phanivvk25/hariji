"""Portal Service: Manages Projects, Pipelines, Environment Governance,
and Versioned Promotions (DEV editable; UAT/PROD read-only).
"""

from typing import Dict, List, Optional
import datetime
from fastapi import HTTPException
from src.core.portal_models import (
    Project,
    Pipeline,
    PipelineNode,
    PipelineEdge,
    EnvironmentType,
    PromotionRequest,
    PromotionRecord,
)


def _create_default_nodes() -> List[PipelineNode]:
    return [
        PipelineNode(
            id="node_trigger",
            name="Inbound Request Trigger",
            type="trigger",
            config={"trigger_type": "api_webhook", "rate_limit": 100},
            position={"x": 50, "y": 150},
        ),
        PipelineNode(
            id="node_orchestrator",
            name="Core Orchestrator (Thinking & Decision)",
            type="orchestrator",
            config={
                "model": "gemini-2.5-flash",
                "thinking_depth": "deep",
                "temperature": 0.2,
                "strategy": "dynamic_plan_and_solve",
                "system_prompt": "You are the Core Orchestrator. Analyze intent, decompose sub-tasks, reason over MCP tools, and verify outputs.",
            },
            position={"x": 280, "y": 150},
        ),
        PipelineNode(
            id="node_mcp_db",
            name="MCP: Postgres Enterprise DB",
            type="mcp_tool",
            config={"server_id": "mcp_db", "transport": "sse", "read_only": False},
            position={"x": 550, "y": 70},
        ),
        PipelineNode(
            id="node_rag_agent",
            name="Knowledge & Policy Agent",
            type="agent",
            config={"model": "gemini-2.5-flash", "capability": "vector_rag", "top_k": 4},
            position={"x": 550, "y": 230},
        ),
        PipelineNode(
            id="node_hitl_gate",
            name="HITL Safety & Risk Gate",
            type="hitl_gate",
            config={
                "risk_threshold": "medium",
                "require_approval_for_write": True,
                "timeout_minutes": 30,
            },
            position={"x": 780, "y": 150},
        ),
        PipelineNode(
            id="node_output",
            name="Synthesized Response Output",
            type="output",
            config={"format": "json_and_markdown", "log_audit": True},
            position={"x": 1000, "y": 150},
        ),
    ]


def _create_default_edges() -> List[PipelineEdge]:
    return [
        PipelineEdge(id="e1", source="node_trigger", target="node_orchestrator", label="Inbound Query"),
        PipelineEdge(id="e2", source="node_orchestrator", target="node_mcp_db", label="Query MCP Tool"),
        PipelineEdge(id="e3", source="node_orchestrator", target="node_rag_agent", label="Policy Lookup"),
        PipelineEdge(id="e4", source="node_mcp_db", target="node_hitl_gate", label="Data Payload"),
        PipelineEdge(id="e5", source="node_rag_agent", target="node_hitl_gate", label="Compliance Context"),
        PipelineEdge(id="e6", source="node_hitl_gate", target="node_output", label="Approved Dispatch"),
    ]


class PortalService:
    def __init__(self):
        self._projects: Dict[str, Project] = {}
        self._promotion_history: List[PromotionRecord] = []
        self._seed_default_projects()

    def _seed_default_projects(self):
        seed_data = [
            (
                "proj_billing",
                "Billing & Dispute Orchestrator",
                "Enterprise fleet managing transaction inquiries, refunds, and compliance auditing.",
                ["finance", "disputes", "mcp-sql"],
            ),
            (
                "proj_cloudops",
                "Cloud Infrastructure Copilot",
                "Multi-cloud telemetry analysis, incident triage, and automated runbook execution.",
                ["devops", "kubernetes", "mcp-cloud"],
            ),
            (
                "proj_custops",
                "Omnichannel Support Fleet",
                "Customer self-service agent with knowledge retrieval, sentiment routing, and escalation.",
                ["support", "rag", "crm"],
            ),
        ]

        for p_id, name, desc, tags in seed_data:
            dev_pipe = Pipeline(
                id=f"{p_id}_dev_v1",
                project_id=p_id,
                environment="dev",
                version="1.0.0",
                is_readonly=False,
                name=f"{name} (DEV)",
                nodes=_create_default_nodes(),
                edges=_create_default_edges(),
            )

            uat_pipe = Pipeline(
                id=f"{p_id}_uat_v1",
                project_id=p_id,
                environment="uat",
                version="1.0.0",
                is_readonly=True,
                name=f"{name} (UAT)",
                nodes=_create_default_nodes(),
                edges=_create_default_edges(),
                promoted_from="dev",
            )

            prod_pipe = Pipeline(
                id=f"{p_id}_prod_v1",
                project_id=p_id,
                environment="prod",
                version="1.0.0",
                is_readonly=True,
                name=f"{name} (PROD)",
                nodes=_create_default_nodes(),
                edges=_create_default_edges(),
                promoted_from="uat",
            )

            project = Project(
                id=p_id,
                name=name,
                description=desc,
                tags=tags,
                pipelines={"dev": dev_pipe, "uat": uat_pipe, "prod": prod_pipe},
            )
            self._projects[p_id] = project

    def list_projects(self) -> List[Project]:
        return list(self._projects.values())

    def get_project(self, project_id: str) -> Project:
        if project_id not in self._projects:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
        return self._projects[project_id]

    def create_project(self, name: str, description: str, tags: Optional[List[str]] = None) -> Project:
        p_id = f"proj_{name.lower().replace(' ', '_')}_{int(datetime.datetime.now().timestamp())}"
        dev_pipe = Pipeline(
            id=f"{p_id}_dev_v1",
            project_id=p_id,
            environment="dev",
            version="1.0.0",
            is_readonly=False,
            name=f"{name} (DEV)",
            nodes=_create_default_nodes(),
            edges=_create_default_edges(),
        )
        uat_pipe = Pipeline(
            id=f"{p_id}_uat_v1",
            project_id=p_id,
            environment="uat",
            version="1.0.0",
            is_readonly=True,
            name=f"{name} (UAT)",
            nodes=_create_default_nodes(),
            edges=_create_default_edges(),
        )
        prod_pipe = Pipeline(
            id=f"{p_id}_prod_v1",
            project_id=p_id,
            environment="prod",
            version="1.0.0",
            is_readonly=True,
            name=f"{name} (PROD)",
            nodes=_create_default_nodes(),
            edges=_create_default_edges(),
        )

        project = Project(
            id=p_id,
            name=name,
            description=description,
            tags=tags or [],
            pipelines={"dev": dev_pipe, "uat": uat_pipe, "prod": prod_pipe},
        )
        self._projects[p_id] = project
        return project

    def get_pipeline(self, project_id: str, environment: EnvironmentType) -> Pipeline:
        proj = self.get_project(project_id)
        if environment not in proj.pipelines:
            raise HTTPException(status_code=404, detail=f"Environment '{environment}' not configured for project.")
        return proj.pipelines[environment]

    def update_dev_pipeline(
        self,
        project_id: str,
        environment: EnvironmentType,
        nodes: List[PipelineNode],
        edges: List[PipelineEdge],
        version: Optional[str] = None,
    ) -> Pipeline:
        """Strict governance check: Only DEV environment can be directly modified."""
        if environment != "dev":
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Governance Violation: Environment '{environment.upper()}' is strictly READ-ONLY. "
                    "All pipeline edits, node additions, and configuration changes must be made in DEV "
                    "and promoted through the governed promotion gate."
                ),
            )

        proj = self.get_project(project_id)
        pipe = proj.pipelines["dev"]
        pipe.nodes = nodes
        pipe.edges = edges
        if version:
            pipe.version = version
        pipe.updated_at = datetime.datetime.now().isoformat()
        return pipe

    def promote_pipeline(self, project_id: str, req: PromotionRequest) -> PromotionRecord:
        """Promote a pipeline from DEV to UAT or UAT to PROD."""
        proj = self.get_project(project_id)

        # Validate legal promotion paths
        valid_paths = [("dev", "uat"), ("uat", "prod"), ("dev", "prod")]
        if (req.source_env, req.target_env) not in valid_paths:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid promotion path from {req.source_env.upper()} to {req.target_env.upper()}.",
            )

        source_pipe = proj.pipelines[req.source_env]
        target_pipe = proj.pipelines[req.target_env]

        # Deep clone nodes & edges to target immutable environment
        target_pipe.nodes = [PipelineNode(**n.model_dump()) for n in source_pipe.nodes]
        target_pipe.edges = [PipelineEdge(**e.model_dump()) for e in source_pipe.edges]
        target_pipe.version = req.version
        target_pipe.promoted_from = req.source_env
        target_pipe.updated_at = datetime.datetime.now().isoformat()

        record = PromotionRecord(
            id=f"promo_{int(datetime.datetime.now().timestamp())}",
            project_id=project_id,
            from_env=req.source_env,
            to_env=req.target_env,
            version=req.version,
            notes=req.notes,
            promoted_by=req.promoted_by,
            status="completed",
        )
        self._promotion_history.insert(0, record)
        return record

    def get_promotion_history(self, project_id: Optional[str] = None) -> List[PromotionRecord]:
        if project_id:
            return [r for r in self._promotion_history if r.project_id == project_id]
        return self._promotion_history


portal_service = PortalService()
