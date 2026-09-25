"""HITL (Human-in-the-Loop) Service: Manages safety policies, risk assessment,
and approval queues for high-risk operations and confidence-threshold interventions.
"""

from typing import Dict, List, Optional
import datetime
from src.core.portal_models import HITLPolicy, HITLApprovalRequest, EnvironmentType


class HITLService:
    def __init__(self):
        self._policies: Dict[str, HITLPolicy] = {}
        self._approvals: Dict[str, HITLApprovalRequest] = {}
        self._seed_default_data()

    def _seed_default_data(self):
        # Default policies for seed projects
        for p_id in ["proj_billing", "proj_cloudops", "proj_custops"]:
            self._policies[p_id] = HITLPolicy(
                id=f"policy_{p_id}",
                project_id=p_id,
                name=f"Enterprise Safety Policy ({p_id})",
                enabled=True,
                require_approval_for_blast_radius="medium",
                confidence_threshold=0.85,
                require_approval_for_promotion=True,
                require_approval_for_tools=[
                    "execute_db_mutation",
                    "delete_cloud_resource",
                    "issue_refund",
                    "scale_down_cluster",
                ],
                auto_reject_timeout_minutes=60,
            )

        # Seed sample pending and completed approvals
        sample_req = HITLApprovalRequest(
            id="appr_001",
            project_id="proj_billing",
            environment="uat",
            run_id="run_uat_7782",
            step_name="MCP: Postgres Enterprise DB",
            action="execute_db_mutation",
            payload={
                "statement": "UPDATE customer_accounts SET dispute_status = 'waived' WHERE account_id = 'ACC-8910';",
                "justification": "Customer refund requested under SLA policy Section 4B.",
            },
            risk_level="high",
            status="pending",
            created_at=datetime.datetime.now().isoformat(),
        )
        self._approvals[sample_req.id] = sample_req

    def get_policy(self, project_id: str) -> HITLPolicy:
        if project_id not in self._policies:
            # Create default policy on demand
            self._policies[project_id] = HITLPolicy(
                id=f"policy_{project_id}",
                project_id=project_id,
                name=f"Policy ({project_id})",
            )
        return self._policies[project_id]

    def update_policy(self, project_id: str, policy: HITLPolicy) -> HITLPolicy:
        self._policies[project_id] = policy
        return policy

    def list_approvals(
        self,
        project_id: Optional[str] = None,
        environment: Optional[EnvironmentType] = None,
        status: Optional[str] = None,
    ) -> List[HITLApprovalRequest]:
        results = list(self._approvals.values())
        if project_id:
            results = [a for a in results if a.project_id == project_id]
        if environment:
            results = [a for a in results if a.environment == environment]
        if status:
            results = [a for a in results if a.status == status]
        return sorted(results, key=lambda x: x.created_at, reverse=True)

    def create_approval_request(
        self,
        project_id: str,
        environment: EnvironmentType,
        run_id: str,
        step_name: str,
        action: str,
        payload: dict,
        risk_level: str = "medium",
    ) -> HITLApprovalRequest:
        appr_id = f"appr_{int(datetime.datetime.now().timestamp())}_{len(self._approvals) + 1}"
        req = HITLApprovalRequest(
            id=appr_id,
            project_id=project_id,
            environment=environment,
            run_id=run_id,
            step_name=step_name,
            action=action,
            payload=payload,
            risk_level=risk_level,  # type: ignore
            status="pending",
            created_at=datetime.datetime.now().isoformat(),
        )
        self._approvals[appr_id] = req
        return req

    def resolve_approval(
        self, approval_id: str, approved: bool, decision_by: str, reason: str
    ) -> HITLApprovalRequest:
        if approval_id not in self._approvals:
            raise KeyError(f"Approval request '{approval_id}' not found.")
        req = self._approvals[approval_id]
        req.status = "approved" if approved else "rejected"
        req.decision_by = decision_by
        req.decision_reason = reason
        return req


hitl_service = HITLService()
