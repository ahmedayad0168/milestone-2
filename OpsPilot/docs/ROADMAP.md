# Development Roadmap

## V0.1 — Working single-agent baseline (included)
- [x] Synthetic SQLite business dataset
- [x] Sales, top products, inventory, customer-order tools
- [x] LlamaIndex policy RAG with ChromaDB
- [x] Gemini ChatGoogleGenerativeAI model adapter
- [x] Restock draft and CSV export tools
- [x] Gradio local UI
- [x] System prompt and unit tests

## V0.2 — Robustness and evaluation
- [ ] Build 40–60 representative business questions with expected tool(s) and expected facts
- [ ] Measure tool-selection accuracy and answer correctness
- [ ] Measure retrieval Hit@k / MRR and citation support
- [ ] Add abstention tests for missing data and out-of-scope actions
- [x] Add controlled retry/backoff for rate limits and provider errors (`GEMINI_MAX_RETRIES` + friendly error mapping)
- [ ] Add per-tool latency and error metrics

## V0.3 — Agent memory and workflow control
- [ ] Add persistent conversation history with user/session isolation
- [ ] Add explicit date-resolution and task-planning nodes
- [ ] Add human approval workflow for restock drafts
- [ ] Add audit log for approvals and rejected requests

## V0.4 — Protocols and integrations
- [ ] Create a read-only MCP server for inventory queries
- [ ] Add supplier/catalog integration in a sandbox
- [ ] Compare LangChain tool wrapper vs. LlamaIndex `QueryEngineTool`
- [ ] Consider `AgentWorkflow` / specialist agents only if task boundaries justify them

## V1.0 — Production hardening
- [ ] FastAPI service, auth, RBAC and tenant isolation
- [ ] PostgreSQL, migrations, backups and data retention
- [ ] Secrets manager, request limits and abuse protection
- [ ] Observability/tracing and security review
- [ ] CI with unit, integration, evaluation and security tests
- [ ] Deployment with staging/production separation and rollback
