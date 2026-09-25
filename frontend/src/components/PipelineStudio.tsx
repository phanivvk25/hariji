import React, { useState } from "react";
import {
  Text,
  Badge,
  Button,
  Input,
  Textarea,
  Spinner,
} from "@fluentui/react-components";
import {
  LockClosed24Regular,
  Save24Regular,
  Play24Regular,
  Add24Regular,
  Delete24Regular,
  Shield24Regular,
  ArrowRight24Regular,
  Sparkle24Regular,
  BoxToolbox24Regular,
  ShieldCheckmark24Regular,
} from "@fluentui/react-icons";
import { useNotification } from "../context/NotificationContext";
import type { Pipeline, PipelineNode, EnvironmentType } from "../types";

interface PipelineStudioProps {
  pipeline: Pipeline | null;
  activeEnv: EnvironmentType;
  loading: boolean;
  onSavePipeline: (nodes: PipelineNode[], edges: any[], version?: string) => Promise<void>;
  onNavigateToRun: () => void;
}

export const PipelineStudio: React.FC<PipelineStudioProps> = ({
  pipeline,
  activeEnv,
  loading,
  onSavePipeline,
  onNavigateToRun,
}) => {
  const { notify, showAlert, showConfirm } = useNotification();
  const isReadOnly = activeEnv !== "dev";
  const [selectedNode, setSelectedNode] = useState<PipelineNode | null>(null);
  const [nodes, setNodes] = useState<PipelineNode[]>(pipeline?.nodes || []);
  const [saving, setSaving] = useState(false);
  const [pipelineVersion, setPipelineVersion] = useState(pipeline?.version || "1.0.0");

  React.useEffect(() => {
    if (pipeline) {
      setNodes(pipeline.nodes);
      setPipelineVersion(pipeline.version);
      if (pipeline.nodes.length > 0 && !selectedNode) {
        setSelectedNode(pipeline.nodes[1] || pipeline.nodes[0]);
      }
    }
  }, [pipeline]);

  const handleUpdateNodeConfig = (key: string, value: any) => {
    if (isReadOnly || !selectedNode) return;
    const updatedNode = {
      ...selectedNode,
      config: { ...selectedNode.config, [key]: value },
    };
    setSelectedNode(updatedNode);
    setNodes((prev) => prev.map((n) => (n.id === updatedNode.id ? updatedNode : n)));
  };

  const handleUpdateNodeName = (name: string) => {
    if (isReadOnly || !selectedNode) return;
    const updated = { ...selectedNode, name };
    setSelectedNode(updated);
    setNodes((prev) => prev.map((n) => (n.id === updated.id ? updated : n)));
  };

  const handleAddNode = () => {
    if (isReadOnly) return;
    const newNode: PipelineNode = {
      id: `node_step_${Date.now()}`,
      name: "Custom Agent Worker",
      type: "agent",
      config: {
        model: "gemini-2.5-flash",
        temperature: 0.3,
        system_prompt: "You are a specialized worker sub-agent assisting the Core Orchestrator.",
      },
      position: { x: 300, y: 300 },
    };
    setNodes((prev) => [...prev, newNode]);
    setSelectedNode(newNode);
  };

  const handleDeleteNode = (nodeToDelete: PipelineNode) => {
    if (isReadOnly) return;
    if (nodeToDelete.type === "orchestrator") {
      showAlert(
        "Cannot Delete Orchestrator",
        "The Core Orchestrator step is required as the primary pipeline coordinator and cannot be deleted.",
        "warning"
      );
      return;
    }

    showConfirm(
      "Confirm Step Deletion",
      `Are you sure you want to delete the step "${nodeToDelete.name}" (${nodeToDelete.id})? This will remove this step and its configuration from the draft pipeline.`,
      () => {
        setNodes((prev) => {
          const updated = prev.filter((n) => n.id !== nodeToDelete.id);
          if (selectedNode?.id === nodeToDelete.id) {
            setSelectedNode(updated.length > 0 ? updated[0] : null);
          }
          return updated;
        });
        notify(
          "Step Deleted",
          `Step "${nodeToDelete.name}" was removed from the draft pipeline.`,
          "success"
        );
      },
      "error",
      "Delete Step",
      "Cancel"
    );
  };

  const handleSave = async () => {
    if (isReadOnly) return;
    setSaving(true);
    try {
      await onSavePipeline(nodes, pipeline?.edges || [], pipelineVersion);
      notify("Pipeline Saved", "DEV Pipeline configuration saved successfully!", "success");
    } catch (err: any) {
      showAlert("Save Error", err.message, "error");
    } finally {
      setSaving(false);
    }
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case "orchestrator":
        return <Sparkle24Regular primaryFill="#0078D4" />;
      case "mcp_tool":
        return <BoxToolbox24Regular primaryFill="#8E562E" />;
      case "hitl_gate":
        return <ShieldCheckmark24Regular primaryFill="#D83B01" />;
      default:
        return <ArrowRight24Regular primaryFill="#107C41" />;
    }
  };

  if (loading) {
    return (
      <div className="tab-loading-state">
        <Spinner label="Loading pipeline configuration..." size="large" />
      </div>
    );
  }

  return (
    <div className="pipeline-studio-container">
      {/* Governance Banner for Read-Only Environments */}
      {isReadOnly ? (
        <div className="governance-readonly-banner">
          <div className="banner-icon">
            <LockClosed24Regular />
          </div>
          <div>
            <strong>IMMUTABLE {activeEnv.toUpperCase()} PIPELINE</strong>
            <div>
              Direct modifications are strictly blocked in {activeEnv.toUpperCase()}. To modify pipelines, switch to the <strong>DEV</strong> environment, edit configurations, test, and promote using the versioned promotion engine.
            </div>
          </div>
        </div>
      ) : (
        <div className="governance-dev-banner">
          <div>
            <strong>🟢 ACTIVE DEV CANVAS (MUTABLE)</strong>
            <div>You have full authoring privileges. Edit node prompts, parameters, and tool bindings freely.</div>
          </div>
          <div style={{ display: "flex", gap: "10px" }}>
            <Button icon={<Add24Regular />} appearance="subtle" size="small" onClick={handleAddNode}>
              Add Step
            </Button>
            <Button
              icon={<Save24Regular />}
              appearance="primary"
              size="small"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? "Saving..." : "Save DEV Pipeline"}
            </Button>
          </div>
        </div>
      )}

      {/* Main Studio Layout: Node Graph (Left) & Inspector (Right) */}
      <div className="studio-split-layout">
        {/* Node Graph Flow View */}
        <div className="node-canvas-view">
          <div className="canvas-header-bar">
            <div>
              <Text weight="semibold">Pipeline Workflow Graph</Text>
              <Text size={200} style={{ marginLeft: "8px", opacity: 0.7 }}>
                Version: {pipelineVersion} ({isReadOnly ? "Locked" : "Draft"})
              </Text>
            </div>
            <Button
              appearance="subtle"
              size="small"
              icon={<Play24Regular />}
              onClick={onNavigateToRun}
            >
              Test Run Pipeline
            </Button>
          </div>

          <div className="nodes-flow-list">
            {nodes.map((node, index) => {
              const isSelected = selectedNode?.id === node.id;
              return (
                <div key={node.id} className="node-flow-item">
                  <div
                    className={`node-card-box ${isSelected ? "selected" : ""} ${
                      node.type === "orchestrator" ? "orchestrator-box" : ""
                    }`}
                    onClick={() => setSelectedNode(node)}
                  >
                    <div className="node-card-top">
                      <div className="node-icon-wrapper">{getNodeIcon(node.type)}</div>
                      <div className="node-info-text">
                        <div className="node-title-row">
                          <span className="node-name">{node.name}</span>
                          {isReadOnly ? (
                            <Badge size="small" color="subtle">Locked</Badge>
                          ) : (
                            node.type !== "orchestrator" && (
                              <Button
                                icon={<Delete24Regular />}
                                appearance="subtle"
                                size="small"
                                className="node-card-delete-btn"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteNode(node);
                                }}
                                title={`Delete step "${node.name}"`}
                              />
                            )
                          )}
                        </div>
                        <span className="node-type-label">{node.type.toUpperCase()}</span>
                      </div>
                    </div>

                    <div className="node-summary-pills">
                      {node.config.model && (
                        <span className="node-param-chip">Model: {node.config.model}</span>
                      )}
                      {node.config.server_id && (
                        <span className="node-param-chip">MCP: {node.config.server_id}</span>
                      )}
                      {node.config.risk_threshold && (
                        <span className="node-param-chip risk-chip">Gate: {node.config.risk_threshold}</span>
                      )}
                    </div>
                  </div>

                  {index < nodes.length - 1 && (
                    <div className="flow-connector-arrow">
                      <div className="connector-line" />
                      <span className="arrow-head">▼</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Node Configuration Inspector */}
        <div className="node-inspector-pane">
          {selectedNode ? (
            <div className="inspector-content">
              <div className="inspector-header">
                <div>
                  <Text weight="bold" size={400}>{selectedNode.name}</Text>
                  <div className="node-id-tag">ID: {selectedNode.id}</div>
                </div>
                {!isReadOnly && selectedNode.type !== "orchestrator" && (
                  <Button
                    icon={<Delete24Regular />}
                    appearance="subtle"
                    size="small"
                    onClick={() => handleDeleteNode(selectedNode)}
                    title={`Delete step "${selectedNode.name}"`}
                  />
                )}
              </div>

              <div className="inspector-fields">
                <div className="field-group">
                  <label className="field-label">Step Name</label>
                  <Input
                    value={selectedNode.name}
                    disabled={isReadOnly}
                    onChange={(_, d) => handleUpdateNodeName(d.value)}
                  />
                </div>

                <div className="field-group">
                  <label className="field-label">Node Type</label>
                  <Badge appearance="tint" color="brand">
                    {selectedNode.type.toUpperCase()}
                  </Badge>
                </div>

                {selectedNode.type === "orchestrator" && (
                  <>
                    <div className="field-group">
                      <label className="field-label">System Prompt / Thinking Strategy</label>
                      <Textarea
                        rows={5}
                        value={selectedNode.config.system_prompt || ""}
                        disabled={isReadOnly}
                        onChange={(_, d) => handleUpdateNodeConfig("system_prompt", d.value)}
                      />
                    </div>
                    <div className="field-group">
                      <label className="field-label">Model Reasoning Level</label>
                      <Input
                        value={selectedNode.config.thinking_depth || "deep"}
                        disabled={isReadOnly}
                        onChange={(_, d) => handleUpdateNodeConfig("thinking_depth", d.value)}
                      />
                    </div>
                  </>
                )}

                {selectedNode.type === "mcp_tool" && (
                  <div className="field-group">
                    <label className="field-label">Target MCP Server</label>
                    <Input
                      value={selectedNode.config.server_id || "mcp_db"}
                      disabled={isReadOnly}
                      onChange={(_, d) => handleUpdateNodeConfig("server_id", d.value)}
                    />
                  </div>
                )}

                {selectedNode.type === "hitl_gate" && (
                  <div className="field-group">
                    <label className="field-label">Intervention Blast Radius</label>
                    <Input
                      value={selectedNode.config.risk_threshold || "medium"}
                      disabled={isReadOnly}
                      onChange={(_, d) => handleUpdateNodeConfig("risk_threshold", d.value)}
                    />
                  </div>
                )}

                <div className="field-group">
                  <label className="field-label">Parameters (Raw JSON)</label>
                  <Textarea
                    rows={4}
                    value={JSON.stringify(selectedNode.config, null, 2)}
                    disabled={isReadOnly}
                    readOnly={isReadOnly}
                    onChange={(_, d) => {
                      try {
                        const parsed = JSON.parse(d.value);
                        setSelectedNode({ ...selectedNode, config: parsed });
                        setNodes((prev) =>
                          prev.map((n) => (n.id === selectedNode.id ? { ...n, config: parsed } : n))
                        );
                      } catch (e) {
                        // wait for valid JSON
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="inspector-placeholder">
              <Shield24Regular style={{ fontSize: "36px", opacity: 0.4 }} />
              <Text>Select any step on the canvas to inspect or configure properties.</Text>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
