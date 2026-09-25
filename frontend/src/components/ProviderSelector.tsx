import React from "react";
import {
  Dropdown,
  Option,
  Text,
  Badge,
  TabList,
  Tab,
} from "@fluentui/react-components";
import type {
  SelectTabData,
  SelectTabEvent,
} from "@fluentui/react-components";
import {
  BrainCircuit20Regular,
  BookSearch20Regular,
  Wrench20Regular,
} from "@fluentui/react-icons";
import type { ProviderInfo, ModelInfo, AgentMode } from "../types";

interface ProviderSelectorProps {
  providers: ProviderInfo[];
  models: Record<string, ModelInfo[]>;
  activeProvider: string;
  activeModel: string;
  agentMode: AgentMode;
  onSelectProvider: (provider: string) => void;
  onSelectModel: (model: string) => void;
  onSelectMode: (mode: AgentMode) => void;
}

export const ProviderSelector: React.FC<ProviderSelectorProps> = ({
  providers,
  models,
  activeProvider,
  activeModel,
  agentMode,
  onSelectProvider,
  onSelectModel,
  onSelectMode,
}) => {
  const currentModelList = models[activeProvider] || [];
  const currentModelInfo = currentModelList.find((m) => m.id === activeModel);

  const handleTabSelect = (_: SelectTabEvent, data: SelectTabData) => {
    onSelectMode(data.value as AgentMode);
  };

  return (
    <div className="fluent-selector-panel">
      {/* Agent Mode Tabs */}
      <div className="fluent-mode-tabs-container">
        <TabList
          selectedValue={agentMode}
          onTabSelect={handleTabSelect}
          size="medium"
          appearance="subtle"
        >
          <Tab value="auto" icon={<BrainCircuit20Regular />}>
            Supervisor (Auto Routing)
          </Tab>
          <Tab value="general" icon={<Wrench20Regular />}>
            General LLM Agent
          </Tab>
          <Tab value="rag" icon={<BookSearch20Regular />}>
            RAG Knowledge Agent
          </Tab>
        </TabList>
      </div>

      {/* Model & Provider Dropdowns */}
      <div className="fluent-provider-controls">
        <div className="fluent-control-group">
          <Text size={200} weight="semibold" className="control-label">
            AI Provider
          </Text>
          <Dropdown
            size="medium"
            value={
              providers.find((p) => p.id === activeProvider)?.name || activeProvider
            }
            selectedOptions={[activeProvider]}
            onOptionSelect={(_, data) => {
              if (data.optionValue) onSelectProvider(data.optionValue);
            }}
          >
            {providers.map((p) => (
              <Option key={p.id} value={p.id} text={p.name}>
                {p.name}
              </Option>
            ))}
          </Dropdown>
        </div>

        <div className="fluent-control-group">
          <Text size={200} weight="semibold" className="control-label">
            Model Selection
          </Text>
          <Dropdown
            size="medium"
            value={currentModelInfo?.name || activeModel}
            selectedOptions={[activeModel]}
            onOptionSelect={(_, data) => {
              if (data.optionValue) onSelectModel(data.optionValue);
            }}
          >
            {currentModelList.map((m) => (
              <Option key={m.id} value={m.id} text={m.name}>
                {m.name}
              </Option>
            ))}
          </Dropdown>
        </div>

        {/* Model Spec Badge Summary */}
        {currentModelInfo && (
          <div className="model-spec-tags">
            <Badge appearance="tint" color="informative" size="small">
              {Math.round(currentModelInfo.context_window / 1000)}k Context
            </Badge>
            {currentModelInfo.supports_tools && (
              <Badge appearance="tint" color="success" size="small">
                Tool Calling
              </Badge>
            )}
            {currentModelInfo.supports_vision && (
              <Badge appearance="tint" color="brand" size="small">
                Vision
              </Badge>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
