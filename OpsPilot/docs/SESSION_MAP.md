# Mapping Your Internship Sessions to OpsPilot

This map is based on the two supplied notebooks: `Copy of research_agent_workshop.ipynb` (LangChain autonomous research workshop; originally written for Groq, OpsPilot uses Gemini) and `02_llamaindex_agents.ipynb` (Building Agents with LlamaIndex).

| Session concept | Where it appears in your notebook(s) | OpsPilot implementation | Next extension |
|---|---|---|---|
| LLM provider + tool calling | Research workshop: ChatGroq and tools | `ChatGoogleGenerativeAI` with `gemini-2.5-flash` | Compare model/tool-call quality with an offline evaluation set |
| ReAct loop / agent | Research workshop: `create_react_agent`; LlamaIndex notebook: `ReActAgent` | LangChain `create_agent` (LangGraph-backed) | Build an explicit custom LangGraph state graph when a fixed workflow is needed |
| Tool design | Research workshop: web, ArXiv, Wikipedia tools | Six business tools + LlamaIndex policy retrieval tool | Add schemas, permission checks, retries and tool-level metrics |
| System prompting | Research workshop: Senior Researcher prompt | OpsPilot prompt with data-grounding and safety boundaries | Add prompt versioning and prompt regression tests |
| Error handling | Research workshop: `ToolNode(handle_tool_errors=True)` | Tool wrappers validate inputs and return controlled error payloads | Centralized retry policy, timeout, circuit breaker |
| Streaming / execution | Research workshop: agent stream and tool activity | Gradio response shows final answer and tool names | Stream intermediate status without exposing chain-of-thought |
| Document loading | LlamaIndex: `SimpleDirectoryReader` | `src/opspilot/rag/ingest.py` | Add PDF, DOCX and CSV parsing with metadata tests |
| Chunking | LlamaIndex: `SentenceSplitter` | `chunk_size=450`, `chunk_overlap=70` | Evaluate chunk size/overlap against a labeled policy QA set |
| Embeddings + vector DB | LlamaIndex: Hugging Face embedding + Chroma | `BAAI/bge-small-en-v1.5` + persistent Chroma | Compare embeddings and retrieval recall / MRR |
| Retrieval / Agentic RAG | LlamaIndex: retriever, query engine, QueryEngineTool | LlamaIndex retriever exposed as an agent tool | Add `QueryEngineTool`/query engine synthesis and compare with current retrieve-then-synthesize flow |
| Evaluation | LlamaIndex: `FaithfulnessEvaluator` | v0.1 starts with deterministic unit tests | Add retrieval hit-rate, citation precision, faithfulness and abstention evals |
| Memory / state | LlamaIndex: `Context`, state management; LangGraph agent state | Recent UI chat history only | Persistent checkpointing scoped by user and conversation |
| MCP | LlamaIndex notebook: MCP server/client example | Not implemented intentionally | Add read-only inventory MCP server and compare tool interoperability |
| Multi-agent | LlamaIndex notebook: `AgentWorkflow` | Not implemented intentionally | Add specialist agents only after a measured need for delegation |

## Compatibility note
The research workshop output itself shows a deprecation warning for `langgraph.prebuilt.create_react_agent` and says it moved to `langchain.agents.create_agent` in LangGraph v1. OpsPilot uses the current `create_agent` entry point while preserving the same core model → tool-call → tool-result → model loop.

## Recommended learning cadence
Add one capability per session, write at least one test for it, and document the trade-off. Do not add MCP, multi-agent orchestration, or a new vector database solely to make the stack look larger.
