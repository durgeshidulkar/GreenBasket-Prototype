import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "greenbasket.db"))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL CHECK(price >= 0),
            stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK(stock_quantity >= 0),
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Completed'
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        """)
        admin = conn.execute("SELECT id FROM admins WHERE username = ?", ("admin",)).fetchone()
        if not admin:
            password = os.environ.get("ADMIN_PASSWORD", "GreenBasket@123")
            conn.execute(
                "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                ("admin", generate_password_hash(password))
            )
        product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if product_count == 0:
            products = [
                ("GB-001", "Organic Tomatoes", "Vegetables", "Fresh, farm-picked organic tomatoes.", 60, 50),
                ("GB-002", "Organic Spinach", "Vegetables", "Tender leafy greens for everyday meals.", 35, 40),
                ("GB-003", "Organic Apples", "Fruits", "Crisp apples sourced from trusted growers.", 180, 25),
                ("GB-004", "Fresh Bananas", "Fruits", "Naturally sweet bananas, ready to enjoy.", 60, 35),
                ("GB-005", "Organic Brown Rice", "Grains", "Wholesome whole-grain brown rice.", 120, 30),
                ("GB-006", "Organic Honey", "Organic Foods", "Golden honey for a naturally sweet touch.", 250, 20),
            ]
            conn.executemany("""
                INSERT INTO products (sku, name, category, description, price, stock_quantity)
                VALUES (?, ?, ?, ?, ?, ?)
            """, products)

def seed_demo_data():
    """Create clearly labelled demonstration sales only when the orders table is empty."""
    with get_db_connection() as conn:
        if conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] > 0:
            return
        products = conn.execute("SELECT id, name, price FROM products WHERE is_active = 1").fetchall()
        product_map = {p["name"]: {"id": p["id"], "price": p["price"]} for p in products}
        demo_orders = [
            [("Organic Tomatoes", 3), ("Organic Spinach", 2)],
            [("Organic Apples", 2), ("Fresh Bananas", 4)],
            [("Organic Brown Rice", 2), ("Organic Honey", 1)],
            [("Organic Tomatoes", 5), ("Fresh Bananas", 3)],
            [("Organic Spinach", 4), ("Organic Apples", 2)],
            [("Organic Brown Rice", 3), ("Organic Honey", 2)],
            [("Organic Tomatoes", 4), ("Organic Apples", 3)],
        ]
        for day, items in enumerate(demo_orders):
            if any(name not in product_map for name, _ in items):
                continue
            total = sum(product_map[name]["price"] * qty for name, qty in items)
            date = (datetime.now() - timedelta(days=6-day)).strftime("%Y-%m-%d %H:%M:%S")
            cur = conn.execute(
                "INSERT INTO orders (order_date, total_amount, status) VALUES (?, ?, 'Completed')",
                (date, total)
            )
            for name, qty in items:
                p = product_map[name]
                conn.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (cur.lastrowid, p["id"], qty, p["price"])
                )
