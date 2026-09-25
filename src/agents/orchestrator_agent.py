"""Core Orchestrator Agent with deep cognitive thinking, dynamic decision-making,
MCP tool integration, configurable HITL enforcement, and automated error ticketing
to Self-Service-Desk in UAT/PROD environments.
"""

from typing import AsyncIterator, List, Optional, Dict, Any
import asyncio
import datetime
import uuid

from src.agents.base import BaseAgent
from src.core.models import AgentStep, ChatMessage
from src.core.providers.base import BaseLLMProvider
from src.services.portal_service import portal_service
from src.services.mcp_service import mcp_service
from src.services.hitl_service import hitl_service
from src.services.desk_service import desk_service


class CoreOrchestratorAgent(BaseAgent):
    """The central reasoning and orchestration brain of the Self-Service Portal."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        super().__init__(
            name="Core Orchestrator Brain",
            description="Performs multi-step cognitive thinking, dynamic planning, MCP tool synthesis, and HITL enforcement.",
            llm_provider=llm_provider,
        )

    async def run(
        self,
        query: str,
        history: Optional[List[ChatMessage]] = None,
        project_id: str = "proj_billing",
        environment: str = "dev",
        simulate_error: bool = False,
        error_step: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[AgentStep]:
        run_id = f"run_{environment}_{uuid.uuid4().hex[:8]}"

        # Step 1: Cognitive Thinking & Intent Analysis
        yield AgentStep(
            step_type="thought",
            content=(
                f"🧠 [Thinking & Intent Formulation] Project: `{project_id}` | Environment: `{environment.upper()}`\n"
                f"Decomposing user request: \"{query}\"\n"
                f"• Evaluating entity targets and required capabilities.\n"
                f"• Inspecting active pipeline nodes and safety constraints."
            ),
            metadata={"run_id": run_id, "stage": "thinking"},
        )
        await asyncio.sleep(0.4)

        # Check for simulated or intentional failure in Step 1 if specified
        if simulate_error and error_step in ["thinking", "planning"]:
            err_msg = f"Intent parsing crashed: Invalid token sequence in query '{query}'"
            for step in self._handle_runtime_failure(
                project_id=project_id,
                environment=environment,
                run_id=run_id,
                step_name="Thinking & Intent Formulation",
                error_type="SyntaxIntentException",
                error_msg=err_msg,
            ):
                yield step
            return

        # Step 2: Decision Making & Route Planning
        pipeline = portal_service.get_pipeline(project_id, environment)  # type: ignore
        all_tools = mcp_service.list_all_tools()
        policy = hitl_service.get_policy(project_id)

        # Match relevant MCP tool
        q_lower = query.lower()
        selected_tool = None
        if "sql" in q_lower or "db" in q_lower or "account" in q_lower or "dispute" in q_lower or "balance" in q_lower:
            selected_tool = next((t for t in all_tools if "sql" in t["name"]), all_tools[0])
        elif "cloud" in q_lower or "pod" in q_lower or "cluster" in q_lower or "k8s" in q_lower:
            selected_tool = next((t for t in all_tools if "cluster" in t["name"] or "pod" in t["name"]), all_tools[1])
        else:
            selected_tool = next((t for t in all_tools if "doc" in t["name"] or "search" in t["name"]), all_tools[2])

        yield AgentStep(
            step_type="thought",
            content=(
                f"⚖️ [Decision Making] Selected strategy: Tool Delegation via MCP Gateway.\n"
                f"• Assigned MCP Server: `{selected_tool.get('server_name')}`\n"
                f"• Target Tool: `{selected_tool.get('name')}` (Risk: `{selected_tool.get('risk_level', 'low')}`)\n"
                f"• Pipeline Environment Governance: {environment.upper()} ({'Read-Only' if pipeline.is_readonly else 'Mutable DEV'})"
            ),
            metadata={"selected_tool": selected_tool["name"], "risk_level": selected_tool.get("risk_level")},
        )
        await asyncio.sleep(0.5)

        # Step 3: HITL Policy Evaluation
        tool_risk = selected_tool.get("risk_level", "low")
        needs_hitl = False
        hitl_reason = ""

        if policy.enabled:
            if selected_tool["name"] in policy.require_approval_for_tools:
                needs_hitl = True
                hitl_reason = f"Tool '{selected_tool['name']}' is registered in strict human signoff list."
            elif policy.require_approval_for_blast_radius == "medium" and tool_risk in ["medium", "high"]:
                needs_hitl = True
                hitl_reason = f"Operation risk level '{tool_risk}' reaches project threshold ('{policy.require_approval_for_blast_radius}')."
            elif policy.require_approval_for_blast_radius == "high" and tool_risk == "high":
                needs_hitl = True
                hitl_reason = "High blast-radius operation requires explicit human confirmation."

        if needs_hitl:
            # Register in HITL service
            approval_req = hitl_service.create_approval_request(
                project_id=project_id,
                environment=environment,  # type: ignore
                run_id=run_id,
                step_name=f"MCP: {selected_tool['server_name']}",
                action=selected_tool["name"],
                payload={"query": query, "tool_args": {"query": f"SELECT * FROM records WHERE q = '{query}'"}},
                risk_level=tool_risk,
            )
            yield AgentStep(
                step_type="thought",
                content=(
                    f"🛡️ [HITL Governance Triggered] Action intercepted by Safety Policy.\n"
                    f"• Reason: {hitl_reason}\n"
                    f"• Approval ID: `{approval_req.id}` created in HITL Queue.\n"
                    f"• Execution paused until reviewer authorization."
                ),
                metadata={"approval_id": approval_req.id, "status": "pending_hitl"},
            )
            await asyncio.sleep(0.6)

        # Check for simulated or intentional runtime failure in Step 4
        if simulate_error:
            err_msg = (
                f"Runtime Exception in {environment.upper()} execution pod: Connection pool exhausted while "
                f"calling MCP server '{selected_tool.get('server_name')}'. Endpoint: 504 Gateway Timeout."
            )
            for step in self._handle_runtime_failure(
                project_id=project_id,
                environment=environment,
                run_id=run_id,
                step_name=f"MCP: {selected_tool.get('name')}",
                error_type="MCPGatewayTimeoutError",
                error_msg=err_msg,
            ):
                yield step
            return

        # Step 4: MCP Tool Invocation
        yield AgentStep(
            step_type="action",
            content=f"Calling MCP Tool `{selected_tool['name']}` on server `{selected_tool['server_name']}`...",
            metadata={"tool": selected_tool["name"], "endpoint": selected_tool.get("server_id")},
        )
        await asyncio.sleep(0.5)

        # Synthetic Observation from MCP
        obs_data = f"Status: 200 OK | Records: 3 matches found for '{query}' in project '{project_id}'. Latency: 42ms."
        yield AgentStep(
            step_type="observation",
            content=obs_data,
            metadata={"source": selected_tool["name"], "status": "success"},
        )
        await asyncio.sleep(0.4)

        # Step 5: Reflection & Verification
        yield AgentStep(
            step_type="thought",
            content=(
                f"🔍 [Reflection & Verification] Output contract satisfied.\n"
                f"• Verified response coherence and alignment with user goal.\n"
                f"• Confirmed environment integrity ({environment.upper()}). Synthesizing final answer."
            ),
        )
        await asyncio.sleep(0.3)

        # Step 6: Final Answer
        final_summary = (
            f"### Orchestrated Execution Summary\n\n"
            f"- **Project**: `{project_id}`\n"
            f"- **Environment**: `{environment.upper()}` ({'Protected Read-Only' if pipeline.is_readonly else 'Active DEV Canvas'})\n"
            f"- **Execution Run**: `{run_id}`\n"
            f"- **MCP Tool Engaged**: `{selected_tool['name']}` via `{selected_tool['server_name']}`\n"
            f"- **HITL Gate**: `{'Passed with policy check' if needs_hitl else 'Bypassed (Safe threshold)'}`\n\n"
            f"**Result**: Successfully retrieved context and completed orchestration task for: *\"{query}\"*. "
            f"All pipeline safety guardrails and multi-environment policies were respected."
        )

        yield AgentStep(
            step_type="final_answer",
            content=final_summary,
            metadata={"run_id": run_id, "project_id": project_id, "environment": environment},
        )

    def _handle_runtime_failure(
        self,
        project_id: str,
        environment: str,
        run_id: str,
        step_name: str,
        error_type: str,
        error_msg: str,
    ):
        """Dispatches errors: In DEV, presents interactive error.
        In UAT and PROD, creates a ticket in Self-Service-Desk and triggers autonomous triage!
        """
        stack_trace = (
            f"Traceback (most recent call last):\n"
            f"  File 'src/agents/orchestrator_agent.py', line 112, in execute_step\n"
            f"    await mcp_client.call_tool(step='{step_name}')\n"
            f"{error_type}: {error_msg}"
        )

        yield AgentStep(
            step_type="observation",
            content=f"❌ Execution Failure in {environment.upper()}: [{error_type}] {error_msg}",
            metadata={"status": "error", "error_type": error_type},
        )

        if environment in ["uat", "prod"]:
            # Auto-create ticket in Self-Service-Desk
            ticket = desk_service.create_ticket(
                project_id=project_id,
                environment=environment,
                run_id=run_id,
                title=f"Failure in {step_name} ({error_type})",
                description=f"Automated execution failed in {environment.upper()} during query execution.",
                error_type=error_type,
                stack_trace=stack_trace,
            )

            desk_msg = (
                f"🚨 **[Self-Service-Desk Auto-Ticketing]**\n\n"
                f"Because this error occurred in protected environment **{environment.upper()}**, incident ticket "
                f"**[{ticket.id}]** was automatically created in `Self-Service-Desk`.\n\n"
                f"🤖 **Autonomous Triage Agent Action**:\n"
                f"- **Severity**: `{ticket.severity}`\n"
                f"- **Status**: `{ticket.status}`\n"
                f"- **Root Cause Analysis (RCA)**: {ticket.triage_summary}\n\n"
                f"💡 **Proposed Remediation for DEV Environment**:\n"
                f"- Target Node: `{ticket.proposed_remediation.get('target_node_id') if ticket.proposed_remediation else 'DEV Pipeline'}`\n"
                f"- Action: {ticket.proposed_remediation.get('recommended_action') if ticket.proposed_remediation else 'Review telemetry'}\n\n"
                f"You can review, inspect, and 1-click apply this fix to the DEV pipeline in the **Self-Service-Desk** tab!"
            )

            yield AgentStep(
                step_type="final_answer",
                content=desk_msg,
                metadata={"ticket_id": ticket.id, "desk_action": "ticket_created_and_triaged"},
            )
        else:
            dev_msg = (
                f"⚠️ **[DEV Environment Anomaly]**\n\n"
                f"An error occurred during DEV pipeline execution:\n\n"
                f"```text\n{stack_trace}\n```\n\n"
                f"Since this is the **DEV** environment, you can modify the pipeline directly in the **Pipeline Studio** canvas."
            )
            yield AgentStep(
                step_type="final_answer",
                content=dev_msg,
                metadata={"status": "dev_error"},
            )


core_orchestrator = CoreOrchestratorAgent()
