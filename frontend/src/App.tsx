import React, { useState, useEffect } from "react";
import {
  FluentProvider,
  webDarkTheme,
  webLightTheme,
  Spinner,
} from "@fluentui/react-components";
import { NotificationProvider, useNotification } from "./context/NotificationContext";
import { PortalTopNav } from "./components/PortalTopNav";
import { PortalFooter } from "./components/PortalFooter";
import { ProjectsList } from "./components/ProjectsList";
import { PipelineStudio } from "./components/PipelineStudio";
import { LiveOrchestrator } from "./components/LiveOrchestrator";
import { MCPToolHub } from "./components/MCPToolHub";
import { HITLGovernance } from "./components/HITLGovernance";
import { SelfServiceDesk } from "./components/SelfServiceDesk";
import {
  fetchProjects,
  createProject,
  fetchPipeline,
  updateDevPipeline,
  promotePipeline,
} from "./api";
import type {
  Project,
  Pipeline,
  PipelineNode,
  EnvironmentType,
  PromotionRequest,
} from "./types";
import "./index.css";

const AppContent: React.FC<{
  darkMode: boolean;
  onToggleTheme: () => void;
}> = ({ darkMode, onToggleTheme }) => {
  const { notify, showAlert } = useNotification();
  const [loading, setLoading] = useState(true);

  // Projects & Multi-Environment State
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [activeEnv, setActiveEnv] = useState<EnvironmentType>("dev");
  const [activeTab, setActiveTab] = useState<string>("pipeline");

  // Pipeline Data State
  const [pipeline, setPipeline] = useState<Pipeline | null>(null);
  const [pipelineLoading, setPipelineLoading] = useState(false);

  // Initial Load of Projects
  const loadInitialProjects = async () => {
    setLoading(true);
    try {
      const projs = await fetchProjects();
      setProjects(projs);
      if (projs.length > 0) {
        const first = projs[0];
        setActiveProject(first);
        loadPipelineData(first.id, "dev");
      }
    } catch (e: any) {
      console.warn("Could not connect to FastAPI backend:", e);
      notify("Backend Notice", "Could not connect to FastAPI backend. Ensure backend is running.", "warning");
    } finally {
      setLoading(false);
    }
  };

  const loadPipelineData = async (projectId: string, env: EnvironmentType) => {
    setPipelineLoading(true);
    try {
      const pipe = await fetchPipeline(projectId, env);
      setPipeline(pipe);
    } catch (e: any) {
      console.warn("Failed to load pipeline:", e);
      notify("Pipeline Load Notice", `Failed to load pipeline for ${env.toUpperCase()}`, "warning");
    } finally {
      setPipelineLoading(false);
    }
  };

  useEffect(() => {
    loadInitialProjects();
  }, []);

  // When project or environment changes, reload pipeline
  const handleSelectProject = (proj: Project) => {
    setActiveProject(proj);
    loadPipelineData(proj.id, activeEnv);
  };

  const handleSelectEnv = (env: EnvironmentType) => {
    setActiveEnv(env);
    if (activeProject) {
      loadPipelineData(activeProject.id, env);
    }
  };

  const handleCreateProject = async (name: string, desc: string) => {
    try {
      const created = await createProject(name, desc);
      setProjects((prev) => [...prev, created]);
      setActiveProject(created);
      setActiveEnv("dev");
      loadPipelineData(created.id, "dev");
      notify("Project Created", `Project "${name}" initialized with DEV, UAT, and PROD pipelines.`, "success");
    } catch (e: any) {
      showAlert("Project Creation Failed", e.message, "error");
    }
  };

  const handleSavePipeline = async (nodes: PipelineNode[], edges: any[], version?: string) => {
    if (!activeProject) return;
    try {
      const updated = await updateDevPipeline(activeProject.id, "dev", nodes, edges, version);
      setPipeline(updated);
      notify("Pipeline Saved", "DEV Pipeline configuration saved successfully.", "success");
    } catch (e: any) {
      showAlert("Save Failed", e.message, "error");
    }
  };

  const handlePromote = async (req: PromotionRequest) => {
    if (!activeProject) return;
    try {
      await promotePipeline(activeProject.id, req);
      // Switch to target environment to verify promoted pipeline
      setActiveEnv(req.target_env);
      await loadPipelineData(activeProject.id, req.target_env);
      notify(
        "Promotion Complete",
        `Successfully promoted ${req.source_env.toUpperCase()} pipeline to ${req.target_env.toUpperCase()} (Version ${req.version})!`,
        "success"
      );
    } catch (e: any) {
      showAlert("Promotion Failed", e.message, "error");
    }
  };

  return (
    <div className="app-layout">
      <PortalTopNav
        darkMode={darkMode}
        onToggleTheme={onToggleTheme}
        projects={projects}
        activeProject={activeProject}
        onSelectProject={handleSelectProject}
        onCreateProject={handleCreateProject}
        activeEnv={activeEnv}
        onSelectEnv={handleSelectEnv}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onPromote={handlePromote}
      />

      <main className="app-main-content" style={{ flex: 1, overflow: "hidden" }}>
        {loading ? (
          <div className="fluent-loading-screen">
            <Spinner label="Connecting to AI Agent Fleet & MCP Gateway..." size="large" />
          </div>
        ) : (
          <>
            {activeTab === "projects" && (
              <ProjectsList
                projects={projects}
                activeProject={activeProject}
                onSelectProject={handleSelectProject}
                onCreateProject={handleCreateProject}
                onNavigateToTab={setActiveTab}
                onSelectEnv={handleSelectEnv}
              />
            )}

            {activeTab === "pipeline" && (
              <PipelineStudio
                pipeline={pipeline}
                activeEnv={activeEnv}
                loading={pipelineLoading}
                onSavePipeline={handleSavePipeline}
                onNavigateToRun={() => setActiveTab("orchestrator")}
              />
            )}

            {activeTab === "orchestrator" && activeProject && (
              <LiveOrchestrator
                projectId={activeProject.id}
                activeEnv={activeEnv}
                onNavigateToDesk={() => setActiveTab("desk")}
              />
            )}

            {activeTab === "mcp" && <MCPToolHub />}

            {activeTab === "hitl" && activeProject && (
              <HITLGovernance projectId={activeProject.id} />
            )}

            {activeTab === "desk" && activeProject && (
              <SelfServiceDesk
                projectId={activeProject.id}
                onNavigateToPipeline={() => {
                  setActiveEnv("dev");
                  setActiveTab("pipeline");
                }}
              />
            )}
          </>
        )}
      </main>

      <PortalFooter activeProject={activeProject} activeEnv={activeEnv} />
    </div>
  );
};

export const App: React.FC = () => {
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
      document.documentElement.classList.remove("light");
      document.body.classList.add("dark");
      document.body.classList.remove("light");
    } else {
      document.documentElement.classList.add("light");
      document.documentElement.classList.remove("dark");
      document.body.classList.add("light");
      document.body.classList.remove("dark");
    }
  }, [darkMode]);

  return (
    <FluentProvider theme={darkMode ? webDarkTheme : webLightTheme} className="fluent-app-root">
      <NotificationProvider>
        <AppContent darkMode={darkMode} onToggleTheme={() => setDarkMode(!darkMode)} />
      </NotificationProvider>
    </FluentProvider>
  );
};

export default App;
