"""LangChain tool wrappers around validated business-service functions."""
import json
from langchain_core.tools import tool

from opspilot.logging_config import get_logger
from opspilot.services import business

logger = get_logger("opspilot.tools")


def _run_tool(name, fn, **kwargs):
    logger.info("tool_call name=%s args=%s", name, kwargs)
    try:
        result = fn(**kwargs)
        return json.dumps(result, ensure_ascii=False, default=str)
    except (ValueError, TypeError) as exc:
        logger.warning("tool_validation_error name=%s error=%s", name, exc)
        return json.dumps({"error": str(exc), "retryable": False}, ensure_ascii=False)
    except Exception:
        logger.exception("tool_execution_error name=%s", name)
        return json.dumps({"error": "The tool failed unexpectedly. Do not invent a result; explain that it could not be completed.", "retryable": True})



@tool
def get_sales_overview(start_date: str, end_date: str) -> str:
    """Get revenue, valid order count, units sold, and average order value for an inclusive date range. Dates must be YYYY-MM-DD."""
    return _run_tool("get_sales_overview", business.sales_overview, start_date=start_date, end_date=end_date)


@tool
def get_top_products(start_date: str, end_date: str, limit: int = 5) -> str:
    """Rank products by revenue for an inclusive date range. Use to identify best-selling products."""
    return _run_tool("get_top_products", business.top_products, start_date=start_date, end_date=end_date, limit=limit)


@tool
def get_low_stock_items() -> str:
    """List products whose stock quantity is at or below their configured reorder level."""
    return _run_tool("get_low_stock_items", business.low_stock_items)


@tool
def lookup_customer_orders(email: str) -> str:
    """Find a demo customer and their most recent orders using the customer's exact email address."""
    return _run_tool("lookup_customer_orders", business.customer_orders, email=email)


@tool
def create_restock_draft(product_id: str, quantity: int, reason: str) -> str:
    """Create a pending restock request JSON for human review. This does NOT place a purchase order or change inventory."""
    return _run_tool("create_restock_draft", business.create_restock_draft,
                     product_id=product_id, quantity=quantity, reason=reason)


@tool
def export_sales_report(start_date: str, end_date: str) -> str:
    """Export sales line items for an inclusive date range to a local CSV file; returns its filename and row count."""
    return _run_tool("export_sales_report", business.export_sales_report, start_date=start_date, end_date=end_date)


BUSINESS_TOOLS = [
    get_sales_overview,
    get_top_products,
    get_low_stock_items,
    lookup_customer_orders,
    create_restock_draft,
    export_sales_report,
]

