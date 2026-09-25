import React, { useState } from "react";
import {
  Text,
  Badge,
  Button,
  Input,
  Checkbox,
  Spinner,
} from "@fluentui/react-components";
import {
  Play24Regular,
  Sparkle24Regular,
  ShieldCheckmark24Regular,
  BoxToolbox24Regular,
  DismissCircle24Regular,
  TicketHorizontal24Regular,
  Eye24Regular,
} from "@fluentui/react-icons";
import { streamOrchestration } from "../api";
import type { AgentStep, EnvironmentType } from "../types";

interface LiveOrchestratorProps {
  projectId: string;
  activeEnv: EnvironmentType;
  onNavigateToDesk: () => void;
}

export const LiveOrchestrator: React.FC<LiveOrchestratorProps> = ({
  projectId,
  activeEnv,
  onNavigateToDesk,
}) => {
  const [query, setQuery] = useState("Execute account balance reconciliation and audit dispute SLA");
  const [isRunning, setIsRunning] = useState(false);
  const [simulateError, setSimulateError] = useState(false);
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [autoTicketId, setAutoTicketId] = useState<string | null>(null);

  const handleRun = async () => {
    if (!query.trim() || isRunning) return;
    setIsRunning(true);
    setSteps([]);
    setAutoTicketId(null);

    const stepAccumulator: AgentStep[] = [];

    try {
      const stream = streamOrchestration(projectId, activeEnv, query, simulateError);
      for await (const step of stream) {
        stepAccumulator.push(step);
        setSteps([...stepAccumulator]);

        if (step.metadata?.ticket_id) {
          setAutoTicketId(step.metadata.ticket_id);
        }
      }
    } catch (err: any) {
      stepAccumulator.push({
        step_type: "observation",
        content: `Stream error: ${err.message}`,
        metadata: { status: "error" },
      });
      setSteps([...stepAccumulator]);
    } finally {
      setIsRunning(false);
    }
  };

  const getStepIcon = (type: string, content: string) => {
    if (content.includes("Thinking")) return <Sparkle24Regular primaryFill="#0078D4" />;
    if (content.includes("Decision")) return <Eye24Regular primaryFill="#8E562E" />;
    if (content.includes("HITL")) return <ShieldCheckmark24Regular primaryFill="#D83B01" />;
    if (type === "action") return <BoxToolbox24Regular primaryFill="#107C41" />;
    if (type === "observation") {
      if (content.includes("❌")) return <DismissCircle24Regular primaryFill="#D13438" />;
      return <Eye24Regular primaryFill="#5C2D91" />;
    }
    return <Sparkle24Regular primaryFill="#0078D4" />;
  };

  return (
    <div className="live-orchestrator-container">
      {/* Top Control Bar */}
      <div className="orchestrator-control-card">
        <div className="orchestrator-query-bar">
          <Input
            className="orchestrator-query-input"
            value={query}
            onChange={(_, d) => setQuery(d.value)}
            placeholder="Type orchestration command or goal..."
            disabled={isRunning}
          />
          <Button
            appearance="primary"
            icon={isRunning ? <Spinner size="tiny" /> : <Play24Regular />}
            onClick={handleRun}
            disabled={isRunning || !query.trim()}
          >
            {isRunning ? "Orchestrating..." : "Execute Pipeline"}
          </Button>
        </div>

        <div className="orchestrator-options-row">
          <div className="options-left">
            <span className="env-run-badge">
              Target: <strong>{activeEnv.toUpperCase()}</strong> ({activeEnv === "dev" ? "Mutable" : "Read-Only"})
            </span>
            <Checkbox
              checked={simulateError}
              onChange={(_, d) => setSimulateError(!!d.checked)}
              label={`Simulate Runtime Error in ${activeEnv.toUpperCase()} (Tests Self-Service-Desk Auto-Ticketing)`}
            />
          </div>

          {autoTicketId && (
            <Button
              appearance="primary"
              size="small"
              icon={<TicketHorizontal24Regular />}
              onClick={onNavigateToDesk}
              style={{ background: "#D13438" }}
            >
              Open Ticket {autoTicketId} in Self-Service-Desk
            </Button>
          )}
        </div>
      </div>

      {/* Real-time Thinking and Execution Stream */}
      <div className="orchestrator-output-area">
        {steps.length === 0 && !isRunning ? (
          <div className="orchestrator-empty-state">
            <Sparkle24Regular style={{ fontSize: "40px", color: "#0078D4", opacity: 0.5 }} />
            <Text weight="semibold" size={400}>Core Orchestrator Ready</Text>
            <Text size={200} style={{ maxWidth: "480px", textAlign: "center", opacity: 0.7 }}>
              Run queries across the multi-agent fleet. The Orchestrator will display its multi-step thinking, evaluate HITL safety rules, invoke MCP servers, and synthesize the result.
            </Text>
          </div>
        ) : (
          <div className="steps-stream-list">
            {steps.map((step, idx) => {
              const isFinal = step.step_type === "final_answer";
              const isThought = step.step_type === "thought";
              return (
                <div
                  key={idx}
                  className={`step-card ${isFinal ? "step-final-card" : ""} ${
                    isThought ? "step-thought-card" : ""
                  }`}
                >
                  <div className="step-card-header">
                    <div className="step-card-title">
                      {getStepIcon(step.step_type, step.content)}
                      <span className="step-type-badge">{step.step_type.toUpperCase()}</span>
                    </div>
                    {step.metadata?.risk_level && (
                      <Badge size="small" color={step.metadata.risk_level === "high" ? "danger" : "informative"}>
                        Risk: {step.metadata.risk_level}
                      </Badge>
                    )}
                  </div>

                  <div className="step-card-body">
                    <pre className="step-content-pre">{step.content}</pre>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
