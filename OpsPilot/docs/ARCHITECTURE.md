# Architecture Notes

## Runtime sequence

1. Gradio receives the user message and the recent session history.
2. `opspilot.agent` calls LangChain `create_agent`, which builds a LangGraph-backed tool loop.
3. The model chooses one or more tools based on the request.
4. Business tools call Python service functions. Those functions validate arguments and issue parameterized SQLite queries.
5. Policy questions call the LlamaIndex retriever. It embeds the query with `BAAI/bge-small-en-v1.5`, searches persistent ChromaDB, and returns top-k chunks with source metadata.
6. The agent synthesizes a final answer from tool results and the system instructions.
7. Gradio shows the answer and the names of tools used; it does not expose hidden reasoning.

## Design decisions

### One agent first
A single agent is sufficient for a bounded demo dataset. Multi-agent systems add coordination and failure modes; introduce them only when a measured use case needs separate specialist responsibilities.

### LlamaIndex as the retrieval layer
The first release uses `SimpleDirectoryReader`, `SentenceSplitter`, `IngestionPipeline`, `HuggingFaceEmbedding`, `ChromaVectorStore`, `VectorStoreIndex`, and a retriever. The retriever is exposed as a LangChain tool so the LangChain agent remains the sole orchestrator.

### No arbitrary SQL
The model selects from fixed business tools. Python owns SQL text, parameter binding, validation, and aggregation semantics.

### Session memory
Recent Gradio chat messages are passed back into the agent for the current UI session. This is short-lived conversation context, not durable long-term memory. A persistent checkpointer and user-scoped conversation store are future work.

## Production evolution
- FastAPI service boundary and versioned request/response schemas.
- AuthN/AuthZ and row-level/tenant-level access controls.
- Managed PostgreSQL and migrations.
- Persistent LangGraph checkpointing with user/session isolation.
- Durable approval workflow with audit events and approver identity.
- OpenTelemetry traces, structured JSON logs, metrics, alerts.
- Offline evaluation set and regression gate for tool selection, correctness, citation support, and abstention.
