from fastapi import HTTPException
from src.services.portal_service import portal_service
from src.services.mcp_service import mcp_service
from src.services.hitl_service import hitl_service
from src.services.desk_service import desk_service
from src.core.portal_models import PromotionRequest, PipelineNode, PipelineEdge


def test_portal_projects_and_environments():
    projects = portal_service.list_projects()
    assert len(projects) >= 3
    proj = projects[0]
    assert "dev" in proj.pipelines
    assert "uat" in proj.pipelines
    assert "prod" in proj.pipelines

    dev_pipe = proj.pipelines["dev"]
    uat_pipe = proj.pipelines["uat"]
    prod_pipe = proj.pipelines["prod"]

    # Immutability flags
    assert dev_pipe.is_readonly is False
    assert uat_pipe.is_readonly is True
    assert prod_pipe.is_readonly is True


def test_strict_governance_immutability():
    projects = portal_service.list_projects()
    p_id = projects[0].id

    # 1. Updating DEV pipeline must succeed
    new_nodes = [
        PipelineNode(
            id="node_custom",
            name="Custom Step in DEV",
            type="agent",
            config={"model": "gemini-2.5-flash"},
        )
    ]
    updated_dev = portal_service.update_dev_pipeline(
        project_id=p_id,
        environment="dev",
        nodes=new_nodes,
        edges=[],
        version="1.1.0-dev",
    )
    assert updated_dev.version == "1.1.0-dev"
    assert len(updated_dev.nodes) == 1

    # 2. Attempting to update UAT directly must raise HTTP 403 Forbidden
    uat_failed = False
    try:
        portal_service.update_dev_pipeline(
            project_id=p_id,
            environment="uat",
            nodes=new_nodes,
            edges=[],
        )
    except HTTPException as exc_uat:
        uat_failed = True
        assert exc_uat.status_code == 403
        assert "READ-ONLY" in exc_uat.detail
    assert uat_failed, "Expected HTTPException 403 for UAT pipeline update"

    # 3. Attempting to update PROD directly must raise HTTP 403 Forbidden
    prod_failed = False
    try:
        portal_service.update_dev_pipeline(
            project_id=p_id,
            environment="prod",
            nodes=new_nodes,
            edges=[],
        )
    except HTTPException as exc_prod:
        prod_failed = True
        assert exc_prod.status_code == 403
        assert "READ-ONLY" in exc_prod.detail
    assert prod_failed, "Expected HTTPException 403 for PROD pipeline update"


def test_pipeline_promotion():
    projects = portal_service.list_projects()
    p_id = projects[0].id

    # Promote DEV -> UAT
    promo_req = PromotionRequest(
        source_env="dev",
        target_env="uat",
        version="1.1.0-rc1",
        notes="Promoting tested custom nodes to UAT staging.",
        promoted_by="Lead Engineer",
    )
    record = portal_service.promote_pipeline(p_id, promo_req)
    assert record.status == "completed"
    assert record.version == "1.1.0-rc1"

    # Verify UAT pipeline has received the changes while remaining read-only
    uat_pipe = portal_service.get_pipeline(p_id, "uat")
    assert uat_pipe.version == "1.1.0-rc1"
    assert uat_pipe.is_readonly is True
    assert len(uat_pipe.nodes) == 1
    assert uat_pipe.nodes[0].name == "Custom Step in DEV"


def test_mcp_service():
    servers = mcp_service.list_servers()
    assert len(servers) >= 3
    tools = mcp_service.list_all_tools()
    assert any(t["name"] == "execute_sql_query" for t in tools)
    assert any(t["name"] == "describe_pods" for t in tools)


def test_hitl_governance():
    p_id = "proj_billing"
    policy = hitl_service.get_policy(p_id)
    assert policy.enabled is True
    assert "execute_db_mutation" in policy.require_approval_for_tools

    # Request approval
    req = hitl_service.create_approval_request(
        project_id=p_id,
        environment="uat",
        run_id="run_test_123",
        step_name="MCP Tool",
        action="execute_db_mutation",
        payload={"query": "DELETE FROM test;"},
        risk_level="high",
    )
    assert req.status == "pending"

    # Resolve approval
    resolved = hitl_service.resolve_approval(
        approval_id=req.id,
        approved=True,
        decision_by="Security Officer",
        reason="Approved for staging test.",
    )
    assert resolved.status == "approved"
    assert resolved.decision_by == "Security Officer"


def test_self_service_desk_and_autonomous_remediation():
    p_id = "proj_billing"

    # Simulate an error in PROD environment
    ticket = desk_service.create_ticket(
        project_id=p_id,
        environment="prod",
        run_id="run_prod_err_999",
        title="MCP Gateway Timeout in Production",
        description="Downstream service failed to respond within 5000ms deadline.",
        error_type="MCPTimeoutException",
        stack_trace="Timeout in worker node",
    )

    assert ticket.severity == "P1"
    assert ticket.environment == "prod"
    # Auto-triage should have executed
    assert ticket.status == "remediation_proposed"
    assert ticket.proposed_remediation is not None
    assert ticket.proposed_remediation["target_environment"] == "dev"

    # Apply remediation to DEV pipeline
    resolved_ticket = desk_service.apply_remediation_to_dev(ticket.id, applied_by="Auto-Remediation Bot")
    assert resolved_ticket.status == "resolved"
    assert resolved_ticket.resolved_at is not None

    # Verify that the DEV pipeline was updated with the fix
    dev_pipe = portal_service.get_pipeline(p_id, "dev")
    assert dev_pipe.updated_at is not None
