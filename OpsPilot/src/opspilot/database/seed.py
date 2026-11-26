"""Deterministic synthetic demo data. No real people or customers are used."""
from datetime import date, timedelta
import random

from opspilot.database.db import get_connection

CUSTOMERS = [
    ("CUS-001", "Maya Hassan", "maya.hassan@example.com", "Cairo"),
    ("CUS-002", "Omar Adel", "omar.adel@example.com", "Alexandria"),
    ("CUS-003", "Laila Samir", "laila.samir@example.com", "Giza"),
    ("CUS-004", "Youssef Nabil", "youssef.nabil@example.com", "Tanta"),
    ("CUS-005", "Nour Khaled", "nour.khaled@example.com", "Mansoura"),
    ("CUS-006", "Salma Hany", "salma.hany@example.com", "Cairo"),
    ("CUS-007", "Ziad Mostafa", "ziad.mostafa@example.com", "Alexandria"),
    ("CUS-008", "Farah Tarek", "farah.tarek@example.com", "Damietta"),
    ("CUS-009", "Adam Fathy", "adam.fathy@example.com", "Ismailia"),
    ("CUS-010", "Jana Ashraf", "jana.ashraf@example.com", "Cairo"),
    ("CUS-011", "Karim Wael", "karim.wael@example.com", "Giza"),
    ("CUS-012", "Malak Ahmed", "malak.ahmed@example.com", "Alexandria"),
]

PRODUCTS = [
    ("SKU-BEAN-01", "House Blend Coffee Beans 1kg", "Coffee", 18.50, 24, 30, "Nile Roasters"),
    ("SKU-BEAN-02", "Single Origin Espresso 1kg", "Coffee", 22.00, 5, 10, "Nile Roasters"),
    ("SKU-CUP-12", "12oz Paper Cups (1000 pcs)", "Packaging", 45.00, 8, 12, "PackRight Supplies"),
    ("SKU-LID-12", "12oz Cup Lids (1000 pcs)", "Packaging", 18.00, 13, 15, "PackRight Supplies"),
    ("SKU-MILK-01", "Oat Milk 1L Case", "Dairy Alternatives", 2.30, 16, 20, "Green Fields"),
    ("SKU-SYR-01", "Chocolate Syrup 1L", "Syrups", 7.90, 50, 15, "TasteCraft"),
    ("SKU-SYR-02", "Vanilla Syrup 1L", "Syrups", 7.50, 9, 12, "TasteCraft"),
    ("SKU-FLTR-01", "Paper Coffee Filters (500 pcs)", "Accessories", 6.20, 33, 20, "Brew Essentials"),
    ("SKU-TEA-01", "English Breakfast Tea (100 bags)", "Tea", 9.80, 11, 15, "Heritage Tea Co"),
    ("SKU-TEA-02", "Green Tea (100 bags)", "Tea", 10.20, 28, 15, "Heritage Tea Co"),
    ("SKU-CAN-01", "Cold Brew Bottle 500ml", "Equipment", 4.40, 7, 10, "PackRight Supplies"),
    ("SKU-CLEAN-01", "Food-safe Surface Cleaner 5L", "Cleaning", 12.00, 18, 10, "CleanPro"),
]


def seed_demo_data() -> None:
    rng = random.Random(20261123)
    today = date(2026, 11, 23)
    statuses = ["delivered", "delivered", "delivered", "shipped", "processing", "cancelled"]
    with get_connection() as conn:
        # Idempotency: re-running the seed command must not duplicate order items.
        existing_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        if existing_orders:
            return
        conn.executemany(
            "INSERT OR IGNORE INTO customers(customer_id, full_name, email, city) VALUES (?, ?, ?, ?)",
            CUSTOMERS,
        )
        conn.executemany(
            """INSERT OR IGNORE INTO products
               (product_id, product_name, category, unit_price, stock_quantity, reorder_level, supplier_name)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            PRODUCTS,
        )
        for n in range(1, 91):
            order_id = f"ORD-{10000+n}"
            customer_id = rng.choice(CUSTOMERS)[0]
            days_ago = rng.randint(0, 59)
            order_date = (today - timedelta(days=days_ago)).isoformat()
            status = rng.choice(statuses)
            conn.execute(
                "INSERT OR IGNORE INTO orders(order_id, customer_id, order_date, status) VALUES (?, ?, ?, ?)",
                (order_id, customer_id, order_date, status),
            )
            chosen = rng.sample(PRODUCTS, k=rng.randint(1, 4))
            for product in chosen:
                quantity = rng.randint(1, 6)
                conn.execute(
                    """INSERT INTO order_items(order_id, product_id, quantity, unit_price)
                       VALUES (?, ?, ?, ?)""",
                    (order_id, product[0], quantity, product[3]),
                )


def main() -> None:
    from opspilot.database.db import initialize_database
    initialize_database()
    print("OpsPilot demo database is ready.")


if __name__ == "__main__":
    main()
