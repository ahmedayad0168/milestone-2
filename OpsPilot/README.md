# OpsPilot — AI Business Operations Agent

OpsPilot is a learning-first, production-oriented starter for an e-commerce operations assistant. A staff member asks a business question in natural language; a single tool-using agent inspects a seeded SQLite database and a company-policy knowledge base, then returns an evidence-grounded answer.

> **Scope of this release:** a local prototype with synthetic demo data. It is not production-ready and it does not connect to real stores, payment systems, suppliers, or customer accounts. It does not execute purchases or mutate inventory.

## 1. Use case

A small e-commerce / retail operator needs one assistant for routine operational questions:

- What were revenue, order count, units sold, and average order value over a date range?
- Which products generated the most sales?
- Which products are at or below their reorder level?
- What are the recent orders for a customer email?
- What does the company policy say about returns, shipping, or purchasing?
- Can the assistant prepare a restock request or export a sales CSV?

The initial agent is **read-only against business records**. The only write actions are safe artifacts: a restock *draft* in `data/approvals/` and a CSV export in `data/reports/`. Neither action places an order or changes stock. A human must review any draft outside the agent.

## 2. LLM and provider

- Provider: **Google Gemini API** (Google AI Studio key; a free tier is available for development in supported regions).
- Default model: `gemini-2.5-flash` (supports tool/function calling). Change it with `GEMINI_MODEL` in `.env`, e.g. to a Pro model for harder questions.
- Framework adapter: `langchain-google-genai` (`ChatGoogleGenerativeAI`).
- Model and provider are configured in `.env`; do not hardcode API keys.
- Rate limits/quotas depend on your key, model, and tier and can change, so check Google AI Studio. Requests are retried with exponential backoff (`GEMINI_MAX_RETRIES`), and quota errors are reported to the user in plain language. Free-tier access is for learning/testing, not a production service.

## 3. Architecture

```text
Gradio Chat UI
      |
      v
LangChain create_agent (LangGraph-backed ReAct loop)
      |                         \
      |                          \--> LlamaIndex Retriever Tool
      |                                SentenceSplitter -> Embeddings
      |                                -> ChromaDB -> top-k policy chunks
      |
      +--> Sales tools ---------> SQLite (parameterized, read-only queries)
      +--> Inventory tools -----> SQLite
      +--> Customer orders ----> SQLite
      +--> Restock draft -------> JSON file (pending review only)
      +--> CSV export ----------> CSV file
```

**Why this split?** LangChain owns the agent loop and tool orchestration. LlamaIndex owns document ingestion, chunking, embeddings, vector storage, and retrieval. The retrieved policy passages are returned as tool evidence; the main agent synthesizes the user-facing answer. This avoids running two independent agent loops in the first release.

## 4. Tools

| Tool | Purpose | Side effect |
|---|---|---|
| `get_sales_overview` | Aggregate sales KPIs for a date range | None |
| `get_top_products` | Rank products by sales for a date range | None |
| `get_low_stock_items` | Find products at/below reorder level | None |
| `lookup_customer_orders` | Look up recent orders by customer email | None |
| `search_company_policies` | Retrieve relevant policy passages with source filenames | None |
| `create_restock_draft` | Write a pending restock request JSON | Draft only; no purchase or stock update |
| `export_sales_report` | Export detailed line items to CSV | Creates a CSV file |

All SQL uses fixed query templates and parameters. There is no arbitrary-SQL tool.

## 5. Requirements

- Python 3.11 or newer (Python 3.12 recommended).
- A Gemini API key for agent responses: <https://aistudio.google.com/apikey>
- Internet access for installing packages and downloading the BGE embedding model on first ingestion.

The business database and unit tests use the Python standard library. LlamaIndex/Chroma and the Gemini adapter are required for the full application.

## 6. Setup (Windows PowerShell)

```powershell
# From the extracted OpsPilot folder
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
Copy-Item .env.example .env
```

Open `.env` and set `GEMINI_API_KEY` (`GOOGLE_API_KEY` also works). Leave `GEMINI_MODEL=gemini-2.5-flash` initially.

Initialize the demo database:

```powershell
python -m opspilot.database.seed
```

Ingest the included company policies into ChromaDB (the first run downloads the embedding model):

```powershell
python -m opspilot.rag.ingest
```

Start the UI:

```powershell
python app.py
```

Then open <http://127.0.0.1:7860>.

## 7. Example prompts

- `Summarize sales from 2026-10-01 to 2026-10-31.`
- `Show the top 5 products by revenue in November 2026.`
- `Which products need replenishment?`
- `Find the recent orders for maya.hassan@example.com.`
- `What is our return policy for an opened product?` 
- `Prepare a restock draft for SKU-CUP-12 with quantity 20; explain why.`
- `Export the sales report from 2026-11-01 to 2026-11-23.`

The seeded data is synthetic and anchored to a demo period ending **2026-11-23**. It is intentionally small enough for local development.

## 8. Tests

The pure business-data layer is tested without calling Gemini or downloading embeddings:

```powershell
pytest -q
```

To manually smoke-test the LLM connection after configuring `.env`:

```powershell
python scripts/check_gemini.py
```

## 9. Important safety and production gaps

Before real business use, add authentication, role-based access control, tenant isolation, secrets management, database migrations, rate limiting, persistent conversation storage, human approval with authenticated identities, audit retention, monitoring/tracing, automated evaluations, backups, and a managed database. Keep the assistant read-only until authorization and approval flows are implemented and tested.

Never commit `.env`, real customer data, or API keys. The notebooks used as learning references contained credentials embedded in cells; revoke any exposed keys and create fresh ones.

## 10. Roadmap

See `docs/ROADMAP.md` and `docs/SESSION_MAP.md` for the staged path to add memory, planning, structured workflows, MCP, LlamaIndex QueryEngineTool/AgentWorkflow, evaluation, observability, and deployment as you cover them in your internship.
