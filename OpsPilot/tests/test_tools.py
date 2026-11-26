"""Tests for the LangChain tool wrappers (JSON contracts and controlled errors)."""
import json

from opspilot.tools.business_tools import BUSINESS_TOOLS


def _tool(name):
    return next(t for t in BUSINESS_TOOLS if t.name == name)


def test_all_expected_tools_registered():
    assert {t.name for t in BUSINESS_TOOLS} == {
        "get_sales_overview", "get_top_products", "get_low_stock_items",
        "lookup_customer_orders", "create_restock_draft", "export_sales_report",
    }


def test_sales_tool_returns_json(demo_db):
    out = json.loads(_tool("get_sales_overview").invoke({"start_date": "2026-10-01", "end_date": "2026-11-23"}))
    assert out["order_count"] > 0 and out["revenue"] > 0


def test_tool_validation_error_is_returned_not_raised(demo_db):
    out = json.loads(_tool("get_sales_overview").invoke({"start_date": "bad", "end_date": "2026-11-23"}))
    assert out["error"] and out["retryable"] is False


def test_restock_tool_rejects_unknown_product(demo_db):
    out = json.loads(_tool("create_restock_draft").invoke(
        {"product_id": "SKU-NOPE", "quantity": 5, "reason": "Testing unknown product"}))
    assert "Unknown product_id" in out["error"]


def test_unknown_customer_is_reported(demo_db):
    out = json.loads(_tool("lookup_customer_orders").invoke({"email": "nobody@example.com"}))
    assert out["found"] is False
