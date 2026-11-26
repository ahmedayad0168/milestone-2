"""Validated business queries and safe file-generation operations."""
from datetime import date, datetime, timezone
import csv
import json
from pathlib import Path
from uuid import uuid4

from opspilot.config import get_settings
from opspilot.database.db import get_connection


def _validate_dates(start_date: str, end_date: str) -> tuple[str, str]:
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("Dates must use YYYY-MM-DD format.") from exc
    if start > end:
        raise ValueError("start_date must be on or before end_date.")
    return start.isoformat(), end.isoformat()


def sales_overview(start_date: str, end_date: str) -> dict:
    start, end = _validate_dates(start_date, end_date)
    sql = """
        SELECT COUNT(DISTINCT o.order_id) AS order_count,
               COALESCE(SUM(oi.quantity), 0) AS units_sold,
               COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) AS revenue
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.order_date BETWEEN ? AND ?
          AND o.status NOT IN ('cancelled', 'refunded')
    """
    with get_connection() as conn:
        row = conn.execute(sql, (start, end)).fetchone()
    order_count = int(row["order_count"] or 0)
    revenue = round(float(row["revenue"] or 0), 2)
    return {
        "start_date": start,
        "end_date": end,
        "order_count": order_count,
        "units_sold": int(row["units_sold"] or 0),
        "revenue": revenue,
        "currency": "USD (demo currency)",
        "average_order_value": round(revenue / order_count, 2) if order_count else 0.0,
        "excluded_statuses": ["cancelled", "refunded"],
    }


def top_products(start_date: str, end_date: str, limit: int = 5) -> list[dict]:
    start, end = _validate_dates(start_date, end_date)
    if not 1 <= int(limit) <= 20:
        raise ValueError("limit must be between 1 and 20.")
    sql = """
        SELECT p.product_id, p.product_name, p.category,
               SUM(oi.quantity) AS units_sold,
               ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.order_date BETWEEN ? AND ?
          AND o.status NOT IN ('cancelled', 'refunded')
        GROUP BY p.product_id, p.product_name, p.category
        ORDER BY revenue DESC
        LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (start, end, int(limit))).fetchall()
    return [dict(row) for row in rows]


def low_stock_items() -> list[dict]:
    sql = """
        SELECT product_id, product_name, category, stock_quantity,
               reorder_level, supplier_name,
               CASE WHEN stock_quantity = 0 THEN 'out_of_stock' ELSE 'reorder' END AS status
        FROM products
        WHERE stock_quantity <= reorder_level
        ORDER BY stock_quantity ASC, product_name ASC
    """
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def customer_orders(email: str, limit: int = 10) -> dict:
    normalized = (email or "").strip().lower()
    if "@" not in normalized or len(normalized) > 254:
        raise ValueError("Provide a valid customer email address.")
    with get_connection() as conn:
        customer = conn.execute(
            "SELECT customer_id, full_name, email, city FROM customers WHERE lower(email) = ?",
            (normalized,),
        ).fetchone()
        if customer is None:
            return {"found": False, "message": "No customer matched that email in the demo database."}
        rows = conn.execute(
            """SELECT o.order_id, o.order_date, o.status,
                      ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0), 2) AS order_total
               FROM orders o LEFT JOIN order_items oi ON oi.order_id = o.order_id
               WHERE o.customer_id = ?
               GROUP BY o.order_id, o.order_date, o.status
               ORDER BY o.order_date DESC LIMIT ?""",
            (customer["customer_id"], max(1, min(int(limit), 20))),
        ).fetchall()
    return {"found": True, "customer": dict(customer), "orders": [dict(row) for row in rows]}


def create_restock_draft(product_id: str, quantity: int, reason: str) -> dict:
    product_id = (product_id or "").strip().upper()
    if not product_id or len(product_id) > 40:
        raise ValueError("Provide a valid product_id.")
    quantity = int(quantity)
    if not 1 <= quantity <= 10000:
        raise ValueError("quantity must be between 1 and 10000.")
    reason = (reason or "").strip()
    if len(reason) < 8 or len(reason) > 500:
        raise ValueError("reason must be between 8 and 500 characters.")
    with get_connection() as conn:
        product = conn.execute(
            "SELECT product_id, product_name, stock_quantity, reorder_level, supplier_name FROM products WHERE product_id = ?",
            (product_id,),
        ).fetchone()
    if product is None:
        raise ValueError("Unknown product_id. Check the inventory tool output for valid IDs.")
    settings = get_settings()
    settings.approvals_dir.mkdir(parents=True, exist_ok=True)
    request_id = f"RST-{uuid4().hex[:10].upper()}"
    payload = {
        "request_id": request_id,
        "status": "PENDING_HUMAN_REVIEW",
        "product": dict(product),
        "requested_quantity": quantity,
        "reason": reason,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "warning": "Draft only. No supplier order was placed and stock was not changed.",
    }
    (settings.approvals_dir / f"{request_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"request_id": request_id, "status": payload["status"], "warning": payload["warning"]}


def export_sales_report(start_date: str, end_date: str) -> dict:
    start, end = _validate_dates(start_date, end_date)
    sql = """
        SELECT o.order_id, o.order_date, o.status, c.full_name, c.email,
               p.product_id, p.product_name, oi.quantity, oi.unit_price,
               ROUND(oi.quantity * oi.unit_price, 2) AS line_total
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.order_date BETWEEN ? AND ?
          AND o.status NOT IN ('cancelled', 'refunded')
        ORDER BY o.order_date, o.order_id
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (start, end)).fetchall()
    settings = get_settings()
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    path = settings.reports_dir / f"sales_report_{start}_to_{end}.csv"
    columns = ["order_id", "order_date", "status", "customer_name", "customer_email",
               "product_id", "product_name", "quantity", "unit_price", "line_total"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row[k] for k in ["order_id", "order_date", "status", "full_name", "email",
                                               "product_id", "product_name", "quantity", "unit_price", "line_total"]])
    return {"file_name": path.name, "row_count": len(rows), "date_range": [start, end],
            "message": "CSV export created locally. It contains synthetic demo data."}
