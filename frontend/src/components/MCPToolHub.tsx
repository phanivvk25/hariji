import React, { useState, useEffect } from "react";
import {
  Card,
  CardHeader,
  Text,
  Badge,
  Button,
  Spinner,
} from "@fluentui/react-components";
import {
  BoxToolbox24Regular,
  ArrowSync24Regular,
} from "@fluentui/react-icons";
import { fetchMCPServers } from "../api";
import type { MCPServerInfo } from "../types";

export const MCPToolHub: React.FC = () => {
  const [servers, setServers] = useState<MCPServerInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const loadServers = async () => {
    setLoading(true);
    try {
      const data = await fetchMCPServers();
      setServers(data);
    } catch (e) {
      console.warn("Could not load MCP servers:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadServers();
  }, []);

  return (
    <div className="mcp-hub-container">
      <div className="hub-top-bar">
        <div>
          <Text weight="bold" size={500}>Model Context Protocol (MCP) Ecosystem</Text>
          <Text size={200} style={{ display: "block", opacity: 0.7 }}>
            Standardized tool discovery, protocol transport (SSE/stdio), and parameter validation schemas.
          </Text>
        </div>
        <Button icon={<ArrowSync24Regular />} appearance="subtle" size="small" onClick={loadServers}>
          Refresh Servers
        </Button>
      </div>

      {loading ? (
        <div className="tab-loading-state">
          <Spinner label="Introspecting MCP servers..." size="large" />
        </div>
      ) : (
        <div className="mcp-servers-grid">
          {servers.map((s) => (
            <Card key={s.id} className="mcp-server-card">
              <CardHeader
                image={<BoxToolbox24Regular primaryFill="#0078D4" style={{ fontSize: "28px" }} />}
                header={<Text weight="semibold" size={400}>{s.name}</Text>}
                description={
                  <div style={{ display: "flex", gap: "6px", alignItems: "center", marginTop: "4px" }}>
                    <Badge appearance="filled" color={s.status === "connected" ? "success" : "danger"} size="small">
                      {s.status.toUpperCase()}
                    </Badge>
                    <Badge appearance="tint" color="brand" size="small">
                      Transport: {s.transport.toUpperCase()}
                    </Badge>
                  </div>
                }
              />

              <div className="mcp-card-body">
                <Text size={200} className="mcp-desc-text">{s.description}</Text>
                <div className="mcp-endpoint-tag">Endpoint: {s.endpoint}</div>

                <div className="mcp-tools-list-section">
                  <Text weight="semibold" size={200} style={{ marginBottom: "8px", display: "block" }}>
                    Discovered Tools ({s.tools.length}):
                  </Text>
                  <div className="mcp-tools-chips">
                    {s.tools.map((t) => (
                      <div key={t.name} className="mcp-tool-chip-row">
                        <div>
                          <strong>{t.name}</strong>
                          <div style={{ fontSize: "11px", opacity: 0.8 }}>{t.description}</div>
                        </div>
                        <Badge
                          size="small"
                          appearance="tint"
                          color={t.risk_level === "high" ? "danger" : t.risk_level === "medium" ? "warning" : "informative"}
                        >
                          {t.risk_level?.toUpperCase() || "LOW"} RISK
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
