import json
from pathlib import Path
import pytest

from opspilot.services.business import (
    sales_overview, top_products, low_stock_items, customer_orders,
    create_restock_draft, export_sales_report,
)


def test_sales_overview_returns_expected_shape(demo_db):
    result = sales_overview("2026-10-01", "2026-10-31")
    assert result["start_date"] == "2026-10-01"
    assert result["order_count"] >= 0
    assert result["revenue"] >= 0
    assert result["currency"] == "USD (demo currency)"


def test_sales_overview_rejects_invalid_range(demo_db):
    with pytest.raises(ValueError):
        sales_overview("2026-11-30", "2026-11-01")


def test_top_products_limit_validation(demo_db):
    with pytest.raises(ValueError):
        top_products("2026-10-01", "2026-10-31", 100)


def test_low_stock_items_only_returns_threshold_breaches(demo_db):
    rows = low_stock_items()
    assert rows
    assert all(row["stock_quantity"] <= row["reorder_level"] for row in rows)


def test_customer_lookup_finds_seeded_customer(demo_db):
    result = customer_orders("maya.hassan@example.com")
    assert result["found"] is True
    assert result["customer"]["email"] == "maya.hassan@example.com"


def test_restock_request_is_draft_only(demo_db, monkeypatch, tmp_path):
    monkeypatch.setenv("OPSILOT_APPROVALS_DIR", str(tmp_path / "approvals"))
    result = create_restock_draft("SKU-CUP-12", 20, "Stock is below the reorder threshold.")
    assert result["status"] == "PENDING_HUMAN_REVIEW"
    payload = json.loads((tmp_path / "approvals" / f"{result['request_id']}.json").read_text())
    assert payload["warning"].startswith("Draft only")
    assert payload["requested_quantity"] == 20


def test_export_sales_report_creates_csv(demo_db, monkeypatch, tmp_path):
    monkeypatch.setenv("OPSILOT_REPORTS_DIR", str(tmp_path / "reports"))
    result = export_sales_report("2026-10-01", "2026-10-31")
    report_path = tmp_path / "reports" / result["file_name"]
    assert report_path.exists()
    assert report_path.read_text(encoding="utf-8-sig").startswith("order_id,order_date")


def test_revenue_excludes_cancelled_orders(demo_db):
    from opspilot.database.db import get_connection
    with get_connection() as conn:
        expected = conn.execute(
            """SELECT ROUND(SUM(oi.quantity*oi.unit_price),2) FROM orders o
               JOIN order_items oi ON oi.order_id=o.order_id
               WHERE o.status NOT IN ('cancelled','refunded')"""
        ).fetchone()[0]
    result = sales_overview("2000-01-01", "2100-01-01")
    assert result["revenue"] == pytest.approx(expected)


def test_restock_draft_validates_inputs(demo_db):
    with pytest.raises(ValueError):
        create_restock_draft("SKU-CUP-12", 0, "Valid reason text")
    with pytest.raises(ValueError):
        create_restock_draft("SKU-CUP-12", 5, "short")
    with pytest.raises(ValueError):
        create_restock_draft("SKU-DOES-NOT-EXIST", 5, "Valid reason text")


def test_customer_lookup_rejects_bad_email(demo_db):
    with pytest.raises(ValueError):
        customer_orders("not-an-email")
