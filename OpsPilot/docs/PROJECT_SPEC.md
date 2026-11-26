# Project Specification

## Problem
Retail/e-commerce staff repeatedly switch between sales exports, inventory lists, order records, and policy documents to answer routine operational questions. OpsPilot provides one natural-language interface over a small, controlled business environment.

## Primary user
An internal operations employee or store manager. The first release has no multi-user authentication, so it must remain local and use synthetic data.

## Goals
1. Translate natural-language questions into a suitable set of safe tools.
2. Retrieve business facts from structured SQLite tables.
3. Retrieve policy evidence from documents with LlamaIndex and ChromaDB.
4. Create useful outputs (restock draft and CSV report) without executing irreversible business actions.
5. Keep the code modular so new internship concepts can be added incrementally.

## Non-goals (v0.1)
- Real supplier integrations or purchasing.
- Payments, refunds, cancellations, or inventory writes.
- Automatic forecasting or machine-learning demand predictions.
- Public multi-tenant SaaS deployment.
- Multi-agent delegation.

## Success criteria for v0.1
- Can answer sales KPI questions from the seeded database.
- Can identify products at/below reorder thresholds.
- Can retrieve the correct policy file passages for policy questions.
- Can create a pending restock JSON without changing stock.
- Can export a date-filtered CSV.
- Business-layer tests pass without API calls.
- Tool errors are surfaced rather than silently converted to facts.

## Data model
`customers` 1—N `orders`; `orders` 1—N `order_items`; `products` 1—N `order_items`.
Revenue = sum(quantity × unit_price) for orders whose status is not `cancelled` or `refunded`. Date filters are inclusive. Currency is synthetic USD for demo consistency.

## Risk controls
- Parameterized SQL only; no natural-language-to-SQL execution.
- Validate dates, limits, IDs, quantities, and reasons in Python.
- Restock tool writes a draft with `PENDING_HUMAN_REVIEW` and cannot place an order.
- Policy claims must be grounded in retrieved text.
- No secrets in source control.
