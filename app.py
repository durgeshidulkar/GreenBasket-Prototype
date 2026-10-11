import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash

from db import get_db_connection, init_db, seed_demo_data

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-for-hosting")

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def home():
    with get_db_connection() as conn:
        products = conn.execute("""
            SELECT id, name, category, description, price, stock_quantity
            FROM products WHERE is_active = 1 ORDER BY category, name
        """).fetchall()
    return render_template("index.html", products=products)

@app.route("/health")
def health():
    return {"status": "ok", "app": "GreenBasket"}

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db_connection() as conn:
            admin = conn.execute(
                "SELECT id, username, password_hash FROM admins WHERE username = ?",
                (username,)
            ).fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("dashboard"))
        flash("Username or password is incorrect.", "danger")
    return render_template("login.html")

@app.route("/admin/dashboard")
@admin_required
def dashboard():
    with get_db_connection() as conn:
        stats = conn.execute("""
            SELECT COUNT(*) AS total_products,
                   COALESCE(SUM(stock_quantity), 0) AS total_stock,
                   COALESCE(SUM(stock_quantity * price), 0) AS inventory_value
            FROM products WHERE is_active = 1
        """).fetchone()
        order_stats = conn.execute("""
            SELECT COUNT(*) AS total_orders,
                   COALESCE(SUM(total_amount), 0) AS revenue
            FROM orders WHERE status = 'Completed'
        """).fetchone()
        category_sales = conn.execute("""
            SELECT p.category, COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS sales
            FROM products p
            LEFT JOIN order_items oi ON oi.product_id = p.id
            LEFT JOIN orders o ON o.id = oi.order_id AND o.status = 'Completed'
            WHERE p.is_active = 1
            GROUP BY p.category ORDER BY sales DESC
        """).fetchall()
        top_products = conn.execute("""
            SELECT p.name, COALESCE(SUM(
                CASE WHEN o.status = 'Completed' THEN oi.quantity ELSE 0 END
            ), 0) AS units_sold
            FROM products p
            LEFT JOIN order_items oi ON oi.product_id = p.id
            LEFT JOIN orders o ON o.id = oi.order_id
            WHERE p.is_active = 1 GROUP BY p.id, p.name
            ORDER BY units_sold DESC, p.name LIMIT 5
        """).fetchall()
        daily_sales = conn.execute("""
            SELECT DATE(order_date) AS sale_date, SUM(total_amount) AS sales
            FROM orders WHERE status = 'Completed'
            GROUP BY DATE(order_date) ORDER BY sale_date
        """).fetchall()
        low_stock = conn.execute("""
            SELECT name, category, stock_quantity,
                   CASE WHEN stock_quantity = 0 THEN 20
                        WHEN stock_quantity <= 5 THEN 15
                        ELSE 10 END AS suggested_restock
            FROM products WHERE is_active = 1 AND stock_quantity <= 10
            ORDER BY stock_quantity ASC
        """).fetchall()
        recent_orders = conn.execute("""
            SELECT id, order_date, total_amount, status
            FROM orders ORDER BY order_date DESC, id DESC LIMIT 5
        """).fetchall()

    daily_labels = [r["sale_date"] for r in daily_sales]
    daily_values = [float(r["sales"] or 0) for r in daily_sales]
    # Simple illustrative next-day estimate: average of available daily totals.
    forecast = round(sum(daily_values) / len(daily_values), 2) if daily_values else 0
    return render_template(
        "dashboard.html",
        username=session.get("admin_username", "Admin"),
        stats=stats, order_stats=order_stats, category_sales=category_sales,
        top_products=top_products, daily_sales=daily_sales, low_stock=low_stock,
        recent_orders=recent_orders, daily_labels=daily_labels,
        daily_values=daily_values, forecast=forecast
    )

@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

with app.app_context():
    init_db()
    seed_demo_data()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
