import React from "react";
import {
  Button,
  Badge,
  Tooltip,
  Text,
} from "@fluentui/react-components";
import {
  Bot24Regular,
  WeatherMoon24Regular,
  WeatherSunny24Regular,
  BookDatabase24Regular,
  Sparkle24Regular,
} from "@fluentui/react-icons";

interface HeaderProps {
  darkMode: boolean;
  onToggleTheme: () => void;
  onOpenKnowledge: () => void;
  activeProvider: string;
  activeModel: string;
}

export const Header: React.FC<HeaderProps> = ({
  darkMode,
  onToggleTheme,
  onOpenKnowledge,
  activeProvider,
  activeModel,
}) => {
  const getProviderColor = (p: string) => {
    switch (p.toLowerCase()) {
      case "google":
        return "success";
      case "openai":
        return "brand";
      case "azure":
        return "informative";
      case "aws_bedrock":
        return "warning";
      default:
        return "subtle";
    }
  };

  const getProviderLabel = (p: string) => {
    switch (p.toLowerCase()) {
      case "google":
        return "Google Gemini";
      case "openai":
        return "OpenAI";
      case "azure":
        return "Microsoft Azure";
      case "aws_bedrock":
        return "Amazon Bedrock";
      default:
        return p;
    }
  };

  return (
    <header className="fluent-header">
      <div className="fluent-header-left">
        <div className="fluent-logo-badge">
          <Bot24Regular primaryFill="#0078D4" />
        </div>
        <div>
          <div className="fluent-title-row">
            <Text weight="bold" size={400} className="fluent-title">
              Enterprise AI Agent Studio
            </Text>
            <Badge appearance="tint" color="brand" shape="rounded" size="small">
              Fluent 2
            </Badge>
          </div>
          <Text size={200} className="fluent-subtitle">
            Hybrid General LLM & Agentic RAG Platform
          </Text>
        </div>
      </div>

      <div className="fluent-header-right">
        <div className="active-model-pill">
          <Sparkle24Regular style={{ color: "#0078D4", fontSize: 16 }} />
          <Text size={200} weight="semibold">
            {getProviderLabel(activeProvider)}
          </Text>
          <span className="dot-divider">•</span>
          <Text size={200} className="model-text">
            {activeModel}
          </Text>
          <Badge
            appearance="filled"
            color={getProviderColor(activeProvider) as any}
            size="small"
            shape="circular"
          />
        </div>

        <Tooltip content="Knowledge Base & RAG Index" relationship="label">
          <Button
            appearance="subtle"
            icon={<BookDatabase24Regular />}
            onClick={onOpenKnowledge}
          >
            Knowledge Base
          </Button>
        </Tooltip>

        <Tooltip
          content={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
          relationship="label"
        >
          <Button
            appearance="subtle"
            icon={darkMode ? <WeatherSunny24Regular /> : <WeatherMoon24Regular />}
            onClick={onToggleTheme}
          />
        </Tooltip>
      </div>
    </header>
  );
};
