import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import {
  Button,
  Badge,
  Menu,
  MenuTrigger,
  MenuList,
  MenuItem,
  MenuPopover,
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
  Input,
  Textarea,
  TabList,
  Tab,
  Text,
} from "@fluentui/react-components";
import {
  WeatherMoon24Regular,
  WeatherSunny24Regular,
  Folder24Regular,
  ArrowUpload24Regular,
  Add24Regular,
  CheckmarkCircle24Regular,
  ShieldLock24Regular,
  Bot24Regular,
  BoxToolbox24Regular,
  ShieldCheckmark24Regular,
  TicketHorizontal24Regular,
  Play24Regular,
  LockClosed20Regular,
} from "@fluentui/react-icons";
import { useNotification } from "../context/NotificationContext";
import type { Project, EnvironmentType, PromotionRequest } from "../types";

interface PortalTopNavProps {
  darkMode: boolean;
  onToggleTheme: () => void;
  projects: Project[];
  activeProject: Project | null;
  onSelectProject: (proj: Project) => void;
  onCreateProject: (name: string, desc: string) => Promise<void>;
  activeEnv: EnvironmentType;
  onSelectEnv: (env: EnvironmentType) => void;
  activeTab: string;
  onSelectTab: (tab: string) => void;
  onPromote: (req: PromotionRequest) => Promise<void>;
}

export const PortalTopNav: React.FC<PortalTopNavProps> = ({
  darkMode,
  onToggleTheme,
  projects,
  activeProject,
  onSelectProject,
  onCreateProject,
  activeEnv,
  onSelectEnv,
  activeTab,
  onSelectTab,
  onPromote,
}) => {
  const { showAlert } = useNotification();
  const [isProjectMenuOpen, setIsProjectMenuOpen] = useState(false);

  useEffect(() => {
    if (isProjectMenuOpen) {
      document.body.classList.add("project-selector-open");
    } else {
      document.body.classList.remove("project-selector-open");
    }
    return () => {
      document.body.classList.remove("project-selector-open");
    };
  }, [isProjectMenuOpen]);
  const [isNewProjectOpen, setIsNewProjectOpen] = useState(false);
  const [newProjName, setNewProjName] = useState("");
  const [newProjDesc, setNewProjDesc] = useState("");

  const [isPromoteOpen, setIsPromoteOpen] = useState(false);
  const [promoVersion, setPromoVersion] = useState("1.1.0");
  const [promoNotes, setPromoNotes] = useState("");
  const [isPromoting, setIsPromoting] = useState(false);

  const handleCreateProjectSubmit = async () => {
    if (!newProjName.trim()) return;
    await onCreateProject(newProjName, newProjDesc);
    setNewProjName("");
    setNewProjDesc("");
    setIsNewProjectOpen(false);
  };

  const handlePromoteSubmit = async () => {
    if (!activeProject) return;
    setIsPromoting(true);
    try {
      const targetEnv: EnvironmentType = activeEnv === "dev" ? "uat" : "prod";
      await onPromote({
        source_env: activeEnv,
        target_env: targetEnv,
        version: promoVersion,
        notes: promoNotes || `Promoted from ${activeEnv.toUpperCase()} to ${targetEnv.toUpperCase()}`,
        promoted_by: "DevOps Lead",
      });
      setIsPromoteOpen(false);
      setPromoNotes("");
    } catch (err: any) {
      showAlert("Promotion Error", err.message, "error");
    } finally {
      setIsPromoting(false);
    }
  };

  return (
    <header className="portal-top-header">
      <div className="portal-header-row">
        {/* Brand & Project Selector */}
        <div className="portal-brand-section">
          <div className="portal-logo-badge">
            <Bot24Regular primaryFill="#0078D4" />
          </div>
          <div>
            <div className="portal-title-row">
              <Text weight="bold" size={400} className="portal-title">
                AI Orchestrator & Self-Service Portal
              </Text>
              <Badge appearance="tint" color="brand" size="small">
                v2.5 Enterprise
              </Badge>
            </div>
            <Text size={200} className="portal-subtitle">
              Model Context Protocol & Multi-Agent Autonomous Fleet
            </Text>
          </div>

          {/* Project Selector Menu with Acrylic Glass & Backdrop Blur */}
          <div className="project-selector-wrapper">
            {isProjectMenuOpen &&
              createPortal(
                <div
                  className={`project-menu-fullscreen-backdrop ${darkMode ? "dark" : "light"}`}
                  onClick={() => setIsProjectMenuOpen(false)}
                  aria-label="Close project menu overlay"
                />,
                document.body
              )}
            <Menu
              open={isProjectMenuOpen}
              onOpenChange={(_, data) => setIsProjectMenuOpen(data.open)}
            >
              <MenuTrigger disableButtonEnhancement>
                <Button
                  icon={<Folder24Regular />}
                  appearance="outline"
                  size="small"
                  className={`project-dropdown-btn ${isProjectMenuOpen ? "active" : ""}`}
                >
                  {activeProject ? activeProject.name : "Select Project"}
                </Button>
              </MenuTrigger>
              <MenuPopover className={`project-menu-popover ${darkMode ? "dark-popover" : "light-popover"}`}>
                <div className="project-menu-header">
                  <Text size={200} weight="semibold" className="project-menu-title">
                    SELECT ENTERPRISE PROJECT
                  </Text>
                  <Badge appearance="tint" color="brand" size="small">
                    {projects.length} Fleets
                  </Badge>
                </div>
                <MenuList className="project-menu-list">
                  {projects.map((p) => {
                    const isSelected = activeProject?.id === p.id;
                    return (
                      <MenuItem
                        key={p.id}
                        onClick={() => {
                          onSelectProject(p);
                          setIsProjectMenuOpen(false);
                        }}
                        className={`project-menu-item ${isSelected ? "selected-project-item" : ""}`}
                        icon={
                          isSelected ? (
                            <CheckmarkCircle24Regular primaryFill="#107C41" />
                          ) : undefined
                        }
                      >
                        <div className="project-menu-item-content">
                          <div className="project-item-title-row">
                            <strong className="project-item-name">{p.name}</strong>
                            <span className="project-item-tag">{p.id}</span>
                          </div>
                          <div className="project-item-desc">{p.description}</div>
                        </div>
                      </MenuItem>
                    );
                  })}
                  <div className="project-menu-divider" />
                  <MenuItem
                    icon={<Add24Regular />}
                    className="project-menu-create-item"
                    onClick={() => {
                      setIsProjectMenuOpen(false);
                      setIsNewProjectOpen(true);
                    }}
                  >
                    <span>Create New Multi-Agent Project...</span>
                  </MenuItem>
                </MenuList>
              </MenuPopover>
            </Menu>
          </div>
        </div>

        {/* Environment Selector with Strict Badges */}
        <div className="portal-env-section">
          <div className="env-badge-group">
            <button
              className={`env-pill env-dev ${activeEnv === "dev" ? "active" : ""}`}
              onClick={() => onSelectEnv("dev")}
              title="Mutable Development Canvas: pipeline, agents, and prompts are editable."
            >
              <span className="env-dot dev-dot" />
              <span>DEV</span>
              <span className="env-mode-tag">Editable</span>
            </button>

            <button
              className={`env-pill env-uat ${activeEnv === "uat" ? "active" : ""}`}
              onClick={() => onSelectEnv("uat")}
              title="Read-Only Staging: pipeline is immutable. Errors trigger Self-Service-Desk tickets."
            >
              <LockClosed20Regular className="env-lock-icon" />
              <span>UAT</span>
              <span className="env-mode-tag">Read-Only</span>
            </button>

            <button
              className={`env-pill env-prod ${activeEnv === "prod" ? "active" : ""}`}
              onClick={() => onSelectEnv("prod")}
              title="Read-Only Production: pipeline is immutable. Errors trigger P1 tickets in Self-Service-Desk."
            >
              <LockClosed20Regular className="env-lock-icon" />
              <span>PROD</span>
              <span className="env-mode-tag">Read-Only</span>
            </button>
          </div>

          {/* Promotion Button */}
          {activeEnv !== "prod" && (
            <Button
              appearance="primary"
              size="small"
              icon={<ArrowUpload24Regular />}
              onClick={() => {
                setPromoVersion("1.1.0");
                setIsPromoteOpen(true);
              }}
            >
              Promote to {activeEnv === "dev" ? "UAT" : "PROD"}
            </Button>
          )}

          {/* Theme Toggle */}
          <Button
            appearance="subtle"
            size="small"
            icon={darkMode ? <WeatherSunny24Regular /> : <WeatherMoon24Regular />}
            onClick={onToggleTheme}
            title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
          />
        </div>
      </div>

      {/* Main Feature Tabs */}
      <div className="portal-nav-tabs">
        <TabList
          selectedValue={activeTab}
          onTabSelect={(_, data) => onSelectTab(data.value as string)}
          size="medium"
        >
          <Tab value="projects" icon={<Folder24Regular />}>
            Projects Portfolio
          </Tab>
          <Tab value="pipeline" icon={<ShieldLock24Regular />}>
            Pipeline Studio {activeEnv !== "dev" && "(Read-Only)"}
          </Tab>
          <Tab value="orchestrator" icon={<Play24Regular />}>
            Live Orchestrator & Thinking
          </Tab>
          <Tab value="mcp" icon={<BoxToolbox24Regular />}>
            MCP Tool Hub
          </Tab>
          <Tab value="hitl" icon={<ShieldCheckmark24Regular />}>
            HITL Governance
          </Tab>
          <Tab value="desk" icon={<TicketHorizontal24Regular />}>
            Self-Service-Desk (Incident & Healing)
          </Tab>
        </TabList>
      </div>

      {/* Create Project Modal */}
      <Dialog open={isNewProjectOpen} onOpenChange={(_, d) => setIsNewProjectOpen(d.open)}>
        <DialogSurface>
          <DialogTitle>Create New Multi-Environment Project</DialogTitle>
          <DialogBody>
            <DialogContent style={{ display: "flex", flexDirection: "column", gap: "14px", marginTop: "10px" }}>
              <Input
                placeholder="Project Name (e.g. Fraud Detection Agent)"
                value={newProjName}
                onChange={(_, d) => setNewProjName(d.value)}
              />
              <Textarea
                placeholder="Project Description & Mission..."
                value={newProjDesc}
                onChange={(_, d) => setNewProjDesc(d.value)}
              />
              <Text size={200} style={{ opacity: 0.8 }}>
                Creating this project will automatically initialize isolated DEV (editable), UAT (read-only), and PROD (read-only) pipelines.
              </Text>
            </DialogContent>
            <DialogActions>
              <Button appearance="secondary" onClick={() => setIsNewProjectOpen(false)}>
                Cancel
              </Button>
              <Button appearance="primary" onClick={handleCreateProjectSubmit} disabled={!newProjName.trim()}>
                Create Project
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>

      {/* Promote Pipeline Modal */}
      <Dialog open={isPromoteOpen} onOpenChange={(_, d) => setIsPromoteOpen(d.open)}>
        <DialogSurface>
          <DialogTitle>
            Promote Pipeline: {activeEnv.toUpperCase()} → {activeEnv === "dev" ? "UAT" : "PROD"}
          </DialogTitle>
          <DialogBody>
            <DialogContent style={{ display: "flex", flexDirection: "column", gap: "14px", marginTop: "10px" }}>
              <div style={{ background: "rgba(0,120,212,0.08)", padding: "12px", borderRadius: "6px" }}>
                <Text size={200}>
                  Promoting will create an immutable, audited snapshot of the current <strong>{activeEnv.toUpperCase()}</strong> pipeline configuration and deploy it to <strong>{activeEnv === "dev" ? "UAT" : "PROD"}</strong>.
                </Text>
              </div>
              <Input
                placeholder="Release Version (e.g. 1.2.0)"
                value={promoVersion}
                onChange={(_, d) => setPromoVersion(d.value)}
              />
              <Textarea
                placeholder="Promotion Notes / Change Summary..."
                value={promoNotes}
                onChange={(_, d) => setPromoNotes(d.value)}
              />
            </DialogContent>
            <DialogActions>
              <Button appearance="secondary" onClick={() => setIsPromoteOpen(false)}>
                Cancel
              </Button>
              <Button appearance="primary" onClick={handlePromoteSubmit} disabled={isPromoting}>
                {isPromoting ? "Promoting..." : "Confirm & Deploy Promotion"}
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </header>
  );
};
