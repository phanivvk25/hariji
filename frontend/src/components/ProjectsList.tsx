import React, { useState } from "react";
import {
  Card,
  CardHeader,
  CardFooter,
  Text,
  Badge,
  Button,
  Input,
  Textarea,
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
} from "@fluentui/react-components";
import {
  Folder24Regular,
  Search24Regular,
  Add24Regular,
  Play24Regular,
  ShieldLock24Regular,
  Tag20Regular,
  CheckmarkCircle20Filled,
} from "@fluentui/react-icons";
import type { Project, EnvironmentType } from "../types";

interface ProjectsListProps {
  projects: Project[];
  activeProject: Project | null;
  onSelectProject: (project: Project) => void;
  onCreateProject: (name: string, desc: string, tags?: string[]) => Promise<void>;
  onNavigateToTab: (tab: string) => void;
  onSelectEnv: (env: EnvironmentType) => void;
}

export const ProjectsList: React.FC<ProjectsListProps> = ({
  projects,
  activeProject,
  onSelectProject,
  onCreateProject,
  onNavigateToTab,
  onSelectEnv,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newProjName, setNewProjName] = useState("");
  const [newProjDesc, setNewProjDesc] = useState("");
  const [newProjTags, setNewProjTags] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const filteredProjects = projects.filter((p) => {
    const q = searchQuery.toLowerCase();
    const nameMatch = p.name.toLowerCase().includes(q);
    const descMatch = p.description.toLowerCase().includes(q);
    const tagMatch = p.tags?.some((t) => t.toLowerCase().includes(q));
    return nameMatch || descMatch || tagMatch;
  });

  const handleOpenStudio = (p: Project) => {
    onSelectProject(p);
    onSelectEnv("dev");
    onNavigateToTab("pipeline");
  };

  const handleOpenRun = (p: Project) => {
    onSelectProject(p);
    onNavigateToTab("orchestrator");
  };

  const handleCreateSubmit = async () => {
    if (!newProjName.trim() || isSubmitting) return;
    setIsSubmitting(true);
    try {
      const parsedTags = newProjTags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      await onCreateProject(newProjName, newProjDesc, parsedTags);
      setNewProjName("");
      setNewProjDesc("");
      setNewProjTags("");
      setIsCreateOpen(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="projects-view-container">
      {/* Top Banner & Search */}
      <div className="projects-header-banner">
        <div className="projects-header-info">
          <div className="projects-icon-badge">
            <Folder24Regular primaryFill="#0078D4" />
          </div>
          <div>
            <Text weight="bold" size={500} className="projects-main-title">
              Enterprise Project Fleet Portfolio
            </Text>
            <Text size={300} className="projects-sub-title">
              Manage multi-agent projects with isolated DEV, UAT, and PROD governance pipelines.
            </Text>
          </div>
        </div>

        <div className="projects-header-actions">
          <Input
            placeholder="Search projects by name, mission, or tags..."
            value={searchQuery}
            onChange={(_, d) => setSearchQuery(d.value)}
            contentBefore={<Search24Regular />}
            style={{ minWidth: 320 }}
          />

          <Button
            appearance="primary"
            icon={<Add24Regular />}
            onClick={() => setIsCreateOpen(true)}
          >
            New Project
          </Button>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="projects-cards-grid">
        {filteredProjects.map((p) => {
          const isActive = activeProject?.id === p.id;
          const devNodesCount = p.pipelines?.dev?.nodes?.length ?? 0;
          const devVersion = p.pipelines?.dev?.version || "1.0.0";
          const uatVersion = p.pipelines?.uat?.version || "1.0.0";
          const prodVersion = p.pipelines?.prod?.version || "1.0.0";

          return (
            <Card
              key={p.id}
              className={`project-portfolio-card ${isActive ? "active-portfolio-card" : ""}`}
            >
              <CardHeader
                header={
                  <div className="project-card-header-row">
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <Text weight="bold" size={400}>
                        {p.name}
                      </Text>
                      {isActive && (
                        <Badge
                          appearance="filled"
                          color="success"
                          icon={<CheckmarkCircle20Filled />}
                          size="small"
                        >
                          ACTIVE WORKSPACE
                        </Badge>
                      )}
                    </div>
                    <Badge appearance="tint" color="brand" size="small">
                      {p.id}
                    </Badge>
                  </div>
                }
                description={
                  <Text size={200} className="project-card-desc">
                    {p.description}
                  </Text>
                }
              />

              <div className="project-card-details">
                {/* Environment Status Row */}
                <div className="env-status-indicators">
                  <div className="env-chip dev-chip">
                    <span className="dot dev-dot" />
                    <span className="env-name">DEV</span>
                    <span className="env-ver">v{devVersion}</span>
                  </div>

                  <div className="env-chip uat-chip">
                    <span className="dot uat-dot" />
                    <span className="env-name">UAT</span>
                    <span className="env-ver">v{uatVersion}</span>
                  </div>

                  <div className="env-chip prod-chip">
                    <span className="dot prod-dot" />
                    <span className="env-name">PROD</span>
                    <span className="env-ver">v{prodVersion}</span>
                  </div>
                </div>

                {/* Tags and Nodes count */}
                <div className="project-meta-row">
                  <div className="project-tags-list">
                    {p.tags?.map((t, idx) => (
                      <Badge key={idx} appearance="outline" shape="rounded" size="small">
                        <Tag20Regular style={{ fontSize: 11, marginRight: 3 }} />
                        {t}
                      </Badge>
                    ))}
                  </div>

                  <Text size={100} className="nodes-counter">
                    {devNodesCount} Pipeline Nodes
                  </Text>
                </div>
              </div>

              <CardFooter className="project-card-footer">
                <Button
                  appearance={isActive ? "primary" : "secondary"}
                  size="small"
                  icon={<ShieldLock24Regular />}
                  onClick={() => handleOpenStudio(p)}
                >
                  Pipeline Studio
                </Button>

                <Button
                  appearance="subtle"
                  size="small"
                  icon={<Play24Regular />}
                  onClick={() => handleOpenRun(p)}
                >
                  Live Run
                </Button>
              </CardFooter>
            </Card>
          );
        })}

        {/* Create New Project Empty Slot */}
        <Card className="new-project-placeholder-card" onClick={() => setIsCreateOpen(true)}>
          <div className="placeholder-content">
            <div className="placeholder-icon-circle">
              <Add24Regular style={{ fontSize: 28, color: "#0078D4" }} />
            </div>
            <Text weight="bold" size={300}>
              Create New Project
            </Text>
            <Text size={200} style={{ color: "#888888", textAlign: "center", maxWidth: 220 }}>
              Initialize a project with isolated DEV, UAT, and PROD agent fleets.
            </Text>
          </div>
        </Card>
      </div>

      {/* Create Project Modal */}
      <Dialog open={isCreateOpen} onOpenChange={(_, d) => setIsCreateOpen(d.open)}>
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
                rows={3}
              />
              <Input
                placeholder="Tags separated by commas (e.g. finance, rag, mcp)"
                value={newProjTags}
                onChange={(_, d) => setNewProjTags(d.value)}
              />
            </DialogContent>
            <DialogActions style={{ marginTop: "18px" }}>
              <Button appearance="secondary" onClick={() => setIsCreateOpen(false)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button
                appearance="primary"
                onClick={handleCreateSubmit}
                disabled={!newProjName.trim() || isSubmitting}
              >
                {isSubmitting ? "Creating..." : "Create Project"}
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  );
};
