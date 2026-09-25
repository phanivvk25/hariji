import React from "react";
import { Badge, Text, Tooltip } from "@fluentui/react-components";
import {
  Sparkle16Regular,
  BookDatabase16Regular,
  ShieldCheckmark16Regular,
  Server16Regular,
  Link16Regular,
} from "@fluentui/react-icons";
import type { EnvironmentType, Project } from "../types";

interface PortalFooterProps {
  activeProject: Project | null;
  activeEnv: EnvironmentType;
}

export const PortalFooter: React.FC<PortalFooterProps> = ({
  activeProject,
  activeEnv,
}) => {
  const getEnvBadgeColor = (env: EnvironmentType) => {
    switch (env) {
      case "dev":
        return "success";
      case "uat":
        return "warning";
      case "prod":
        return "danger";
    }
  };

  return (
    <footer className="portal-footer">
      {/* Left side: System status & environment */}
      <div className="portal-footer-left">
        <div className="status-indicator-item">
          <span className="live-status-dot" />
          <Text size={200} weight="semibold" className="footer-status-text">
            Agent Fleet: Operational
          </Text>
        </div>

        <span className="footer-separator">•</span>

        <div className="status-indicator-item">
          <Server16Regular style={{ color: "#0078D4", fontSize: 13 }} />
          <Text size={200} className="footer-sub-text">
            FastAPI: 127.0.0.1:8000
          </Text>
        </div>

        <span className="footer-separator">•</span>

        <div className="status-indicator-item">
          <Text size={200} className="footer-sub-text">
            Workspace: <strong>{activeProject?.name || "None Selected"}</strong>
          </Text>
          <Badge
            appearance="filled"
            color={getEnvBadgeColor(activeEnv) as any}
            size="small"
            shape="rounded"
          >
            {activeEnv.toUpperCase()}
          </Badge>
        </div>
      </div>

      {/* Right side: telemetry, RAG, and docs */}
      <div className="portal-footer-right">
        <div className="status-indicator-item">
          <BookDatabase16Regular style={{ color: "#107C41", fontSize: 13 }} />
          <Text size={200} className="footer-sub-text">
            Vector Store: Ready
          </Text>
        </div>

        <span className="footer-separator">•</span>

        <div className="status-indicator-item">
          <ShieldCheckmark16Regular style={{ color: "#D83B01", fontSize: 13 }} />
          <Text size={200} className="footer-sub-text">
            HITL Governance: Active
          </Text>
        </div>

        <span className="footer-separator">•</span>

        <div className="status-indicator-item">
          <Sparkle16Regular style={{ color: "#0078D4", fontSize: 13 }} />
          <Text size={200} className="footer-sub-text">
            v2.5 Enterprise (Fluent 2)
          </Text>
        </div>

        <span className="footer-separator">•</span>

        <Tooltip content="Open OpenAPI / Swagger Docs" relationship="label">
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="footer-doc-link"
          >
            <Link16Regular style={{ fontSize: 12 }} />
            <span>API Docs</span>
          </a>
        </Tooltip>
      </div>
    </footer>
  );
};
