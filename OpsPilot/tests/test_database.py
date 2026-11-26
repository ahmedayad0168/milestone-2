from opspilot.database.db import get_connection


def test_database_has_seeded_tables(demo_db):
    with get_connection() as conn:
        customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    assert customers == 12
    assert products == 12
    assert orders == 90
