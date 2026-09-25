import React, { useState, useEffect } from "react";
import {
  Card,
  CardHeader,
  Text,
  Badge,
  Button,
  Input,
  Switch,
  Spinner,
} from "@fluentui/react-components";
import {
  ShieldCheckmark24Regular,
  Checkmark24Regular,
  Dismiss24Regular,
  ArrowSync24Regular,
} from "@fluentui/react-icons";
import {
  fetchHITLPolicy,
  updateHITLPolicy,
  fetchHITLApprovals,
  resolveHITLApproval,
} from "../api";
import { useNotification } from "../context/NotificationContext";
import type { HITLPolicy, HITLApprovalRequest } from "../types";

interface HITLGovernanceProps {
  projectId: string;
}

export const HITLGovernance: React.FC<HITLGovernanceProps> = ({ projectId }) => {
  const { notify, showAlert } = useNotification();
  const [policy, setPolicy] = useState<HITLPolicy | null>(null);
  const [approvals, setApprovals] = useState<HITLApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingPolicy, setSavingPolicy] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [pol, apprs] = await Promise.all([
        fetchHITLPolicy(projectId),
        fetchHITLApprovals(projectId),
      ]);
      setPolicy(pol);
      setApprovals(apprs);
    } catch (e) {
      console.warn(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId]);

  const handleSavePolicy = async () => {
    if (!policy) return;
    setSavingPolicy(true);
    try {
      await updateHITLPolicy(projectId, policy);
      notify("Policy Saved", "HITL Governance Policy updated successfully.", "success");
    } catch (e: any) {
      showAlert("Policy Update Error", e.message, "error");
    } finally {
      setSavingPolicy(false);
    }
  };

  const handleResolve = async (approvalId: string, approved: boolean) => {
    try {
      await resolveHITLApproval(approvalId, approved, "Lead Architect", "Evaluated by security policy.");
      notify(
        approved ? "Action Authorized" : "Action Rejected",
        approved
          ? "Intervention request approved and scheduled for execution."
          : "Intervention request rejected.",
        approved ? "success" : "warning"
      );
      await loadData();
    } catch (e: any) {
      showAlert("Approval Error", e.message, "error");
    }
  };

  if (loading) {
    return (
      <div className="tab-loading-state">
        <Spinner label="Loading HITL Governance Center..." size="large" />
      </div>
    );
  }

  return (
    <div className="hitl-container">
      {/* Top Description */}
      <div className="hub-top-bar">
        <div>
          <Text weight="bold" size={500}>Human-in-the-Loop (HITL) Governance Center</Text>
          <Text size={200} style={{ display: "block", opacity: 0.7 }}>
            Define intervention thresholds, blast-radius gates, and authorize high-impact operations.
          </Text>
        </div>
        <Button icon={<ArrowSync24Regular />} appearance="subtle" size="small" onClick={loadData}>
          Refresh Queue
        </Button>
      </div>

      <div className="hitl-split-layout">
        {/* Left: Policy Configuration */}
        {policy && (
          <Card className="hitl-policy-card">
            <CardHeader
              image={<ShieldCheckmark24Regular primaryFill="#0078D4" style={{ fontSize: "26px" }} />}
              header={<Text weight="semibold" size={400}>Safety Policy Configuration</Text>}
              description={<Text size={200} style={{ opacity: 0.7 }}>Project: {projectId}</Text>}
            />

            <div className="policy-form-body">
              <div className="field-group">
                <Switch
                  checked={policy.enabled}
                  onChange={(_, d) => setPolicy({ ...policy, enabled: d.checked })}
                  label="Enable Global HITL Enforcement"
                />
              </div>

              <div className="field-group">
                <label className="field-label">Blast-Radius Trigger Level</label>
                <select
                  className="native-select-input"
                  value={policy.require_approval_for_blast_radius}
                  onChange={(e) =>
                    setPolicy({
                      ...policy,
                      require_approval_for_blast_radius: e.target.value as any,
                    })
                  }
                >
                  <option value="low">Low (Intervene on all operations)</option>
                  <option value="medium">Medium (Intervene on writes & mutations)</option>
                  <option value="high">High (Intervene on destructive deletions only)</option>
                </select>
              </div>

              <div className="field-group">
                <label className="field-label">Confidence Score Cutoff (0.0 - 1.0)</label>
                <Input
                  type="number"
                  step="0.05"
                  min="0.5"
                  max="1.0"
                  value={policy.confidence_threshold.toString()}
                  onChange={(_, d) =>
                    setPolicy({ ...policy, confidence_threshold: parseFloat(d.value) || 0.85 })
                  }
                />
                <span className="field-hint">
                  Decisions with reasoning confidence below this cutoff are paused for human review.
                </span>
              </div>

              <div className="field-group">
                <Switch
                  checked={policy.require_approval_for_promotion}
                  onChange={(_, d) =>
                    setPolicy({ ...policy, require_approval_for_promotion: d.checked })
                  }
                  label="Require Sign-off for Environment Promotions (DEV → UAT → PROD)"
                />
              </div>

              <Button
                appearance="primary"
                size="small"
                onClick={handleSavePolicy}
                disabled={savingPolicy}
              >
                {savingPolicy ? "Saving Policy..." : "Update Governance Policy"}
              </Button>
            </div>
          </Card>
        )}

        {/* Right: Pending & Historic Approvals */}
        <div className="hitl-approvals-panel">
          <Text weight="semibold" size={400} style={{ marginBottom: "12px", display: "block" }}>
            Intervention & Approval Queue ({approvals.length})
          </Text>

          {approvals.length === 0 ? (
            <div className="empty-approvals-box">
              <Checkmark24Regular style={{ fontSize: "32px", color: "#107C41" }} />
              <Text>No pending interventions. All pipelines running within configured risk bounds.</Text>
            </div>
          ) : (
            <div className="approvals-cards-list">
              {approvals.map((req) => (
                <div key={req.id} className="approval-card">
                  <div className="approval-card-top">
                    <div>
                      <strong>{req.action}</strong>
                      <div className="approval-meta-row">
                        <Badge size="small" appearance="tint" color="brand">
                          Env: {req.environment.toUpperCase()}
                        </Badge>
                        <Badge
                          size="small"
                          color={req.risk_level === "high" ? "danger" : "warning"}
                        >
                          Risk: {req.risk_level.toUpperCase()}
                        </Badge>
                        <span className="step-name-chip">{req.step_name}</span>
                      </div>
                    </div>

                    <Badge
                      appearance="filled"
                      color={
                        req.status === "approved"
                          ? "success"
                          : req.status === "rejected"
                          ? "danger"
                          : "warning"
                      }
                    >
                      {req.status.toUpperCase()}
                    </Badge>
                  </div>

                  <div className="approval-payload-box">
                    <pre>{JSON.stringify(req.payload, null, 2)}</pre>
                  </div>

                  {req.status === "pending" && (
                    <div className="approval-actions-row">
                      <Button
                        appearance="primary"
                        size="small"
                        icon={<Checkmark24Regular />}
                        onClick={() => handleResolve(req.id, true)}
                      >
                        Authorize & Proceed
                      </Button>
                      <Button
                        appearance="secondary"
                        size="small"
                        icon={<Dismiss24Regular />}
                        onClick={() => handleResolve(req.id, false)}
                      >
                        Reject Action
                      </Button>
                    </div>
                  )}

                  {req.decision_by && (
                    <div className="approval-decision-info">
                      Resolved by: <strong>{req.decision_by}</strong> ({req.decision_reason})
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
