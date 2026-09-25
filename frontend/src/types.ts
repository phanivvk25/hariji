export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  description: string;
  context_window: number;
  supports_vision: boolean;
  supports_tools: boolean;
  is_default: boolean;
}

export interface ProviderInfo {
  id: string;
  name: string;
  default_model: string;
}

export interface ModelsResponse {
  providers: ProviderInfo[];
  models: Record<string, ModelInfo[]>;
  active: {
    provider: string;
    model: string;
  };
}

export type AgentMode = "auto" | "general" | "rag";

export interface AgentStep {
  step_type: "thought" | "action" | "observation" | "citation" | "final_answer";
  content: string;
  metadata?: Record<string, any>;
}

export interface ChatMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  steps?: AgentStep[];
  citations?: Array<{
    source: string;
    score: number;
    page?: number;
    content: string;
  }>;
  timestamp: string;
  provider?: string;
  model?: string;
}

export interface KnowledgeStats {
  total_chunks: number;
  sources_count: number;
  sources: string[];
  active_embedder: string;
  vector_backend: string;
}

// --- Self-Service Portal & Desk Types ---

export type EnvironmentType = "dev" | "uat" | "prod";
export type SeverityType = "P1" | "P2" | "P3";
export type TicketStatus = "open" | "in_triage" | "remediation_proposed" | "resolved";
export type ApprovalStatus = "pending" | "approved" | "rejected";

export interface PipelineNode {
  id: string;
  name: string;
  type: "trigger" | "orchestrator" | "agent" | "mcp_tool" | "hitl_gate" | "output";
  config: Record<string, any>;
  position: { x: number; y: number };
}

export interface PipelineEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

export interface Pipeline {
  id: string;
  project_id: string;
  environment: EnvironmentType;
  version: string;
  is_readonly: boolean;
  name: string;
  nodes: PipelineNode[];
  edges: PipelineEdge[];
  updated_at: string;
  promoted_from?: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
  tags: string[];
  pipelines: Record<EnvironmentType, Pipeline>;
}

export interface PromotionRequest {
  source_env: EnvironmentType;
  target_env: EnvironmentType;
  version: string;
  notes: string;
  promoted_by: string;
}

export interface PromotionRecord {
  id: string;
  project_id: string;
  from_env: EnvironmentType;
  to_env: EnvironmentType;
  version: string;
  notes: string;
  promoted_at: string;
  promoted_by: string;
  status: string;
}

export interface MCPServerInfo {
  id: string;
  name: string;
  description: string;
  transport: "stdio" | "sse" | "http";
  endpoint: string;
  status: "connected" | "disconnected" | "error";
  tools_count: number;
  tools: Array<{
    name: string;
    description: string;
    parameters?: Record<string, any>;
    risk_level?: "low" | "medium" | "high";
  }>;
}

export interface HITLPolicy {
  id: string;
  project_id: string;
  name: string;
  enabled: boolean;
  require_approval_for_blast_radius: "low" | "medium" | "high";
  confidence_threshold: number;
  require_approval_for_promotion: boolean;
  require_approval_for_tools: string[];
  auto_reject_timeout_minutes: number;
}

export interface HITLApprovalRequest {
  id: string;
  project_id: string;
  environment: EnvironmentType;
  run_id: string;
  step_name: string;
  action: string;
  payload: Record<string, any>;
  risk_level: "low" | "medium" | "high";
  status: ApprovalStatus;
  created_at: string;
  decision_by?: string;
  decision_reason?: string;
}

export interface DeskTicket {
  id: string;
  project_id: string;
  environment: "uat" | "prod";
  run_id: string;
  title: string;
  description: string;
  error_type: string;
  stack_trace: string;
  severity: SeverityType;
  status: TicketStatus;
  created_at: string;
  resolved_at?: string;
  triage_summary?: string;
  auto_healed?: boolean;
  remediation_time_ms?: number;
  itsm_sync?: {
    system: string;
    ticket_ref: string;
    synced_at: string;
    status: string;
  };
  preventive_guardrail?: string;
  proposed_remediation?: {
    target_environment: string;
    target_node_id: string;
    recommended_action: string;
    config_patch: Record<string, any>;
  };
}

export interface DeskMetrics {
  total_incidents: number;
  resolved_incidents: number;
  auto_healed_count: number;
  auto_healing_rate_pct: number;
  avg_mttr_ms: number;
  sla_compliance_pct: number;
  active_open_count: number;
  active_engine_status: string;
}

