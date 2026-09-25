import type {
  ModelsResponse,
  AgentMode,
  AgentStep,
  KnowledgeStats,
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
  EnvironmentType,
} from "./types";

const API_BASE = "http://127.0.0.1:8000/api";
const PORTAL_BASE = `${API_BASE}/portal`;

// --- Standard Chat & Knowledge APIs ---

export async function fetchModels(): Promise<ModelsResponse> {
  const res = await fetch(`${API_BASE}/models`);
  if (!res.ok) throw new Error("Failed to load models");
  return res.json();
}

export async function selectModel(provider: string, model: string): Promise<any> {
  const res = await fetch(`${API_BASE}/models/select`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, model }),
  });
  if (!res.ok) throw new Error("Failed to select model");
  return res.json();
}

export async function fetchKnowledgeStats(): Promise<KnowledgeStats> {
  const res = await fetch(`${API_BASE}/knowledge/stats`);
  if (!res.ok) throw new Error("Failed to load knowledge stats");
  return res.json();
}

export async function uploadDocument(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/knowledge/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload document");
  return res.json();
}

export async function queryKnowledge(query: string, top_k = 4): Promise<any> {
  const res = await fetch(`${API_BASE}/knowledge/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k }),
  });
  if (!res.ok) throw new Error("Failed to query knowledge");
  return res.json();
}

export async function reindexDirectory(): Promise<any> {
  const res = await fetch(`${API_BASE}/knowledge/ingest/directory`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to reindex directory");
  return res.json();
}

export async function* streamChat(
  query: string,
  mode: AgentMode,
  provider?: string,
  model?: string
): AsyncGenerator<AgentStep> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, mode, provider, model }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat error: ${response.statusText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("data: ")) {
        try {
          const jsonStr = trimmed.slice(6);
          const step: AgentStep = JSON.parse(jsonStr);
          yield step;
        } catch (e) {
          console.warn("Failed to parse SSE step:", e);
        }
      }
    }
  }
}

// --- Self-Service Portal APIs ---

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${PORTAL_BASE}/projects`);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function createProject(name: string, description: string, tags: string[] = []): Promise<Project> {
  const res = await fetch(`${PORTAL_BASE}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description, tags }),
  });
  if (!res.ok) throw new Error("Failed to create project");
  return res.json();
}

export async function fetchPipeline(projectId: string, env: EnvironmentType): Promise<Pipeline> {
  const res = await fetch(`${PORTAL_BASE}/projects/${projectId}/pipelines/${env}`);
  if (!res.ok) throw new Error(`Failed to load pipeline for ${env.toUpperCase()}`);
  return res.json();
}

export async function updateDevPipeline(
  projectId: string,
  env: EnvironmentType,
  nodes: PipelineNode[],
  edges: PipelineEdge[],
  version?: string
): Promise<Pipeline> {
  const res = await fetch(`${PORTAL_BASE}/projects/${projectId}/pipelines/${env}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nodes, edges, version }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || `Failed to update pipeline in ${env.toUpperCase()}`);
  }
  return res.json();
}

export async function promotePipeline(
  projectId: string,
  req: PromotionRequest
): Promise<PromotionRecord> {
  const res = await fetch(`${PORTAL_BASE}/projects/${projectId}/promote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || "Promotion failed");
  }
  return res.json();
}

export async function fetchPromotions(projectId?: string): Promise<PromotionRecord[]> {
  const url = projectId ? `${PORTAL_BASE}/promotions?project_id=${projectId}` : `${PORTAL_BASE}/promotions`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch promotion logs");
  return res.json();
}

// --- MCP Registry APIs ---

export async function fetchMCPServers(): Promise<MCPServerInfo[]> {
  const res = await fetch(`${PORTAL_BASE}/mcp/servers`);
  if (!res.ok) throw new Error("Failed to load MCP servers");
  return res.json();
}

export async function fetchAllMCPTools(): Promise<any[]> {
  const res = await fetch(`${PORTAL_BASE}/mcp/tools`);
  if (!res.ok) throw new Error("Failed to load MCP tools");
  const data = await res.json();
  return data.tools || [];
}

// --- HITL Governance APIs ---

export async function fetchHITLPolicy(projectId: string): Promise<HITLPolicy> {
  const res = await fetch(`${PORTAL_BASE}/hitl/policy/${projectId}`);
  if (!res.ok) throw new Error("Failed to load HITL policy");
  return res.json();
}

export async function updateHITLPolicy(projectId: string, policy: HITLPolicy): Promise<HITLPolicy> {
  const res = await fetch(`${PORTAL_BASE}/hitl/policy/${projectId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(policy),
  });
  if (!res.ok) throw new Error("Failed to update HITL policy");
  return res.json();
}

export async function fetchHITLApprovals(
  projectId?: string,
  env?: EnvironmentType,
  status?: string
): Promise<HITLApprovalRequest[]> {
  const params = new URLSearchParams();
  if (projectId) params.append("project_id", projectId);
  if (env) params.append("environment", env);
  if (status) params.append("status", status);

  const res = await fetch(`${PORTAL_BASE}/hitl/approvals?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to load HITL approvals");
  return res.json();
}

export async function resolveHITLApproval(
  approvalId: string,
  approved: boolean,
  decisionBy: string = "Platform Lead",
  reason: string = "Verified and authorized."
): Promise<HITLApprovalRequest> {
  const res = await fetch(`${PORTAL_BASE}/hitl/approvals/${approvalId}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved, decision_by: decisionBy, reason }),
  });
  if (!res.ok) throw new Error("Failed to resolve approval request");
  return res.json();
}

// --- Self-Service-Desk APIs ---

export async function fetchDeskTickets(
  projectId?: string,
  env?: string,
  status?: string
): Promise<DeskTicket[]> {
  const params = new URLSearchParams();
  if (projectId) params.append("project_id", projectId);
  if (env) params.append("environment", env);
  if (status) params.append("status", status);

  const res = await fetch(`${PORTAL_BASE}/desk/tickets?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to load Self-Service-Desk tickets");
  return res.json();
}

export async function triageDeskTicket(ticketId: string): Promise<DeskTicket> {
  const res = await fetch(`${PORTAL_BASE}/desk/tickets/${ticketId}/triage`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to trigger triage agent");
  return res.json();
}

export async function applyDeskRemediation(ticketId: string): Promise<DeskTicket> {
  const res = await fetch(`${PORTAL_BASE}/desk/tickets/${ticketId}/apply-remediation`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to apply remediation to DEV pipeline");
  return res.json();
}

export async function autoHealDeskTicket(ticketId: string): Promise<DeskTicket> {
  const res = await fetch(`${PORTAL_BASE}/desk/tickets/${ticketId}/auto-heal`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to execute autonomous auto-heal");
  return res.json();
}

export async function autoHealAllDeskTickets(projectId?: string): Promise<{
  healed_count: number;
  tickets: DeskTicket[];
  avg_mttr_ms: number;
  message: string;
}> {
  const params = new URLSearchParams();
  if (projectId) params.append("project_id", projectId);
  const res = await fetch(`${PORTAL_BASE}/desk/auto-heal-all?${params.toString()}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to execute batch auto-heal");
  return res.json();
}

export async function simulateTelemetryAnomaly(
  projectId: string,
  environment?: "uat" | "prod",
  anomalyType?: string
): Promise<DeskTicket> {
  const res = await fetch(`${PORTAL_BASE}/desk/simulate-telemetry-anomaly`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: projectId,
      environment: environment || "uat",
      anomaly_type: anomalyType,
    }),
  });
  if (!res.ok) throw new Error("Failed to simulate telemetry anomaly");
  return res.json();
}

export async function fetchDeskMetrics(projectId?: string): Promise<DeskMetrics> {
  const params = new URLSearchParams();
  if (projectId) params.append("project_id", projectId);
  const res = await fetch(`${PORTAL_BASE}/desk/metrics?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch desk operational metrics");
  return res.json();
}

// --- Core Orchestrator Run Streaming ---

export async function* streamOrchestration(
  projectId: string,
  environment: EnvironmentType,
  query: string,
  simulateError: boolean = false,
  errorStep?: string
): AsyncGenerator<AgentStep> {
  const response = await fetch(`${PORTAL_BASE}/orchestrate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: projectId,
      environment,
      query,
      simulate_error: simulateError,
      error_step: errorStep,
    }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Orchestration error: ${response.statusText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("data: ")) {
        try {
          const jsonStr = trimmed.slice(6);
          const step: AgentStep = JSON.parse(jsonStr);
          yield step;
        } catch (e) {
          console.warn("Failed to parse SSE step:", e);
        }
      }
    }
  }
}
