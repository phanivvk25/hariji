import React, { useState, useRef, useEffect } from "react";
import {
  Card,
  Text,
  Badge,
  Button,
  Textarea,
  Persona,
  Accordion,
  AccordionItem,
  AccordionHeader,
  AccordionPanel,
} from "@fluentui/react-components";
import {
  Send24Regular,
  BrainCircuit20Regular,
  BookDatabase16Regular,
  Lightbulb16Regular,
  Sparkle20Regular,
} from "@fluentui/react-icons";
import type { ChatMessageItem, AgentMode, AgentStep } from "../types";

interface ChatInterfaceProps {
  messages: ChatMessageItem[];
  isStreaming: boolean;
  activeSteps: AgentStep[];
  onSendMessage: (query: string) => void;
  agentMode: AgentMode;
  activeProvider: string;
  activeModel: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  isStreaming,
  activeSteps,
  onSendMessage,
  agentMode,
  activeProvider,
  activeModel,
}) => {
  const [inputText, setInputText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeSteps]);

  const handleSend = () => {
    if (!inputText.trim() || isStreaming) return;
    const q = inputText.trim();
    setInputText("");
    onSendMessage(q);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickPrompts = [
    "What are the chunk size and overlap guidelines in Chapter 3?",
    "Calculate 128 * 4 + 64 / 2",
    "What AI providers are supported and what is the policy on credentials?",
    "What is the current time and system status?",
  ];

  return (
    <div className="fluent-chat-container">
      {/* Messages Scroll Area */}
      <div className="fluent-messages-area">
        {messages.length === 0 ? (
          <div className="fluent-empty-chat">
            <div className="empty-sparkle-icon">
              <Sparkle20Regular style={{ fontSize: 36, color: "#0078D4" }} />
            </div>
            <Text size={500} weight="bold" className="empty-title">
              How can I assist your workflow today?
            </Text>
            <Text size={300} className="empty-subtitle">
              Seamlessly orchestrate General LLM Agents, Tool execution, and RAG Knowledge retrieval.
            </Text>

            <div className="quick-prompts-grid">
              {quickPrompts.map((p, idx) => (
                <Card
                  key={idx}
                  className="quick-prompt-card"
                  onClick={() => onSendMessage(p)}
                >
                  <div className="quick-prompt-header">
                    <Lightbulb16Regular style={{ color: "#0078D4" }} />
                    <Text size={200} weight="semibold">
                      Suggested Query
                    </Text>
                  </div>
                  <Text size={200} className="quick-prompt-text">
                    "{p}"
                  </Text>
                </Card>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              className={`fluent-message-row ${
                m.role === "user" ? "user-row" : "assistant-row"
              }`}
            >
              {m.role === "assistant" && (
                <Persona
                  presence={{ status: "available" }}
                  name="AI Agent"
                  size="small"
                  avatar={{ color: "brand" }}
                />
              )}

              <div className="fluent-message-bubble-wrapper">
                <Card
                  className={`fluent-message-bubble ${
                    m.role === "user" ? "user-bubble" : "assistant-bubble"
                  }`}
                >
                  {/* Assistant Header Info */}
                  {m.role === "assistant" && (
                    <div className="assistant-bubble-meta">
                      <Badge appearance="tint" color="brand" size="small">
                        {m.provider || activeProvider} • {m.model || activeModel}
                      </Badge>
                      <Text size={100} className="timestamp-text">
                        {m.timestamp}
                      </Text>
                    </div>
                  )}

                  {/* Prior Reasoning Steps / Thoughts Accordion */}
                  {m.steps && m.steps.length > 0 && (
                    <Accordion collapsible className="fluent-reasoning-accordion">
                      <AccordionItem value="reasoning">
                        <AccordionHeader size="small">
                          <BrainCircuit20Regular style={{ marginRight: 6, color: "#0078D4" }} />
                          <Text size={200} weight="semibold">
                            Agent Reasoning Steps ({m.steps.length})
                          </Text>
                        </AccordionHeader>
                        <AccordionPanel>
                          <div className="reasoning-steps-timeline">
                            {m.steps.map((st, sidx) => (
                              <div key={sidx} className={`timeline-step step-${st.step_type}`}>
                                <div className="step-pill">
                                  {st.step_type === "thought" && "💭 Thought"}
                                  {st.step_type === "action" && "⚡ Tool Action"}
                                  {st.step_type === "observation" && "👁 Observation"}
                                  {st.step_type === "citation" && "📖 Citation"}
                                </div>
                                <Text size={200} className="step-content">
                                  {st.content}
                                </Text>
                              </div>
                            ))}
                          </div>
                        </AccordionPanel>
                      </AccordionItem>
                    </Accordion>
                  )}

                  {/* Citations Cards if RAG Grounded */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="citations-tray">
                      <Text size={200} weight="semibold" className="citations-title">
                        <BookDatabase16Regular style={{ marginRight: 4 }} />
                        Grounded Document Citations ({m.citations.length}):
                      </Text>
                      <div className="citations-chips">
                        {m.citations.map((c, cidx) => (
                          <Card key={cidx} className="citation-chip-card">
                            <div className="citation-chip-top">
                              <Badge appearance="filled" color="informative" size="small">
                                {Math.round(c.score * 100)}% match
                              </Badge>
                              <Text size={100} weight="semibold">
                                {c.source} {c.page ? `(p. ${c.page})` : ""}
                              </Text>
                            </div>
                            <Text size={100} className="citation-chip-content">
                              {c.content}
                            </Text>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Final Content */}
                  <div className="message-content-text">
                    <Text size={300} style={{ whiteSpace: "pre-wrap" }}>
                      {m.content}
                    </Text>
                  </div>
                </Card>
              </div>

              {m.role === "user" && (
                <Persona
                  name="User"
                  size="small"
                  avatar={{ color: "colorful" }}
                />
              )}
            </div>
          ))
        )}

        {/* Live Active Streaming Step Card */}
        {isStreaming && (
          <div className="fluent-message-row assistant-row">
            <Persona
              presence={{ status: "busy" }}
              name="AI Agent"
              size="small"
              avatar={{ color: "brand" }}
            />
            <div className="fluent-message-bubble-wrapper">
              <Card className="fluent-message-bubble assistant-bubble streaming-bubble">
                <div className="streaming-header">
                  <Sparkle20Regular className="rotating-sparkle" />
                  <Text size={200} weight="semibold">
                    Agent is processing...
                  </Text>
                  <Badge appearance="tint" color="warning" size="small">
                    Live
                  </Badge>
                </div>

                <div className="streaming-steps-list">
                  {activeSteps.map((st, idx) => (
                    <div key={idx} className={`timeline-step step-${st.step_type}`}>
                      <span className="step-tag">[{st.step_type.toUpperCase()}]</span>
                      <Text size={200}>{st.content}</Text>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar Area */}
      <div className="fluent-input-dock">
        <div className="input-wrapper">
          <Textarea
            resize="none"
            placeholder={
              agentMode === "rag"
                ? "Ask questions grounded in uploaded documents..."
                : agentMode === "general"
                ? "Ask reasoning queries, tool calculations, or web search tasks..."
                : "Ask any question (Supervisor will automatically route to RAG or General)..."
            }
            value={inputText}
            onChange={(_, data) => setInputText(data.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            rows={2}
            className="fluent-chat-textarea"
          />

          <div className="input-footer-row">
            <Text size={100} className="mode-indicator-hint">
              Mode: <strong>{agentMode.toUpperCase()}</strong> | Model:{" "}
              <strong>{activeModel}</strong>
            </Text>

            <Button
              appearance="primary"
              icon={<Send24Regular />}
              disabled={!inputText.trim() || isStreaming}
              onClick={handleSend}
            >
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
