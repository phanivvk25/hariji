# Hariji

**AI Agent Orchestrator Portal** — an autonomous, multi-agent cognitive platform built with enterprise-grade SDLC governance, blast-radius controls, and self-healing infrastructure.

---

## Overview

Hariji is a cognitive multi-agent orchestration platform designed for enterprises that need AI systems to reason, act, and recover — not just execute pre-scripted steps. A Supervisor Agent coordinates specialized RAG, General, and Triage agents through a Thought → Action → Observation → Synthesis reasoning loop, executing standardized tools via the open **Model Context Protocol (MCP)**, with strict environment promotion gates and autonomous incident remediation built in from the ground up.

## Key Capabilities

- 🧠 **Cognitive multi-agent reasoning** — a Supervisor Agent dynamically routes work across specialized agents rather than following a static, pre-defined flow
- 🏗️ **Enterprise SDLC lifecycle** — a strict three-tier `DEV → UAT → PROD` promotion pipeline, with staging and production environments cryptographically locked against live edits
- 🔧 **Open standards, no lock-in** — built natively on the Model Context Protocol (MCP), supporting `stdio`, `sse`, and `http` transports
- 🛡️ **Human-in-the-loop governance** — every action is scored by blast radius, with confidence-threshold gating and tool-level whitelisting for high-impact operations
- ⚡ **Autonomous self-healing** — runtime anomalies are triaged, root-caused, and patched into the DEV pipeline automatically, with ITSM sync (ServiceNow/PagerDuty) and sub-second mean time to remediation
- 📚 **Native enterprise RAG** — a localized vector store with cosine similarity thresholding and provenance-grounded retrieval
- 🔀 **Multi-provider LLM orchestration** — live switching across OpenAI, Anthropic, Gemini, DeepSeek, and local Ollama models

## Architecture

| Component | Description |
|---|---|
| Supervisor Agent | Cognitive router coordinating specialized worker agents |
| RAG Agent | Retrieves grounded enterprise knowledge from the vector store |
| General Agent | Decomposes complex goals into iterative ReAct steps |
| Triage Agent | Autonomously analyzes runtime anomalies and synthesizes patches |
| Pipeline Studio | Visual, mutable DEV-environment pipeline editor |
| Promotion Engine | Semantic-versioned, audited promotion across DEV → UAT → PROD |
| HITL Governance Engine | Blast-radius scoring and approval gating for sensitive actions |
| MCP Tool Hub | Standardized, vendor-neutral tool and resource integration layer |

## Getting Started

```bash
# Clone the repository
git clone https://github.com/<your-org>/hariji.git
cd hariji

# Install dependencies
# (add project-specific setup steps here)

# Configure environment variables
cp .env.example .env

# Run locally
# (add run/start command here)
```

> Fill in the setup steps above with Hariji's actual install/run commands once finalized.

## License

Hariji is licensed under the **Elastic License 2.0 (ELv2)** — a source-available license, not a traditional open-source license. In plain terms:

**You can:**
- View, use, and modify the source code freely
- Run Hariji internally within your own organization, including in production
- Build on top of it, extend it, and contribute back

**You cannot:**
- Offer Hariji (or a modified version of it) as a hosted or managed service to third parties
- Circumvent or remove any license-key-gated functionality
- Remove or obscure copyright, licensing, or trademark notices

This means Hariji is free to use and adapt for your own organization's needs, but competitors cannot take the code and resell it as their own competing SaaS product.

See the [LICENSE](./LICENSE) file for the full legal text, or the [Elastic License 2.0 FAQ](https://www.elastic.co/licensing/elastic-license/faq) for common-scenario clarifications (the FAQ is written for Elastic's own products, but the underlying terms are identical).

## Contact

Built by **Phaneendra Varanasi** 

For licensing questions, partnership inquiries, or early access, reach out via LinkedIn or open an issue.
