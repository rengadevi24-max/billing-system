"""
Departmental Store Billing System - Backend
Flask + MySQL

Run:
    pip install -r requirements.txt
    (make sure MySQL is running and schema.sql has been imported)
    python app.py

Server runs on: http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory, session, redirect
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
from functools import wraps

from config import DB_CONFIG, SECRET_KEY

app = Flask(__name__, static_folder="../", static_url_path="")
app.secret_key = SECRET_KEY
CORS(app, supports_credentials=True)  # allow frontend (different port / file) to call this API

# Pages that don't require login
PUBLIC_PAGES = {"/login.html", "/register.html", "/style.css"}


@app.before_request
def require_login_for_pages():
    """
    Protects the billing pages no matter how they're accessed
    (root '/', '/index.html', '/stock-details.html', etc.).
    Login/Register pages, static assets, and API routes are left open
    here; individual API routes use @login_required where needed.
    """
    path = request.path
    if path.startswith("/api/"):
        return None  # API routes handle their own auth via @login_required
    if path in PUBLIC_PAGES:
        return None
    if path.endswith(".js") or path.endswith(".css"):
        return None
    if "user_id" not in session:
        return redirect("/login.html")
    return None


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def login_required(f):
    """Decorator to protect API routes so only logged-in users can use them."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Not logged in"}), 401
        return f(*args, **kwargs)
    return wrapper


# ------------------------------------------------------------------
# Serve the frontend (index.html, style.css, script.js) from the
# same server so you don't hit CORS issues while testing.
# Main billing page is protected - must be logged in.
# ------------------------------------------------------------------
@app.route("/")
def serve_index():
    if "user_id" not in session:
        return redirect("/login.html")
    return send_from_directory(app.static_folder, "index.html")


# ================== AUTH: REGISTER / LOGIN / LOGOUT ==================

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    store_name = data.get("store_name")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not store_name or not username or not password:
        return jsonify({"error": "Store name, ID and password are required"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "This ID is already taken. Please choose another."}), 400

        password_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (store_name, username, email, password_hash) VALUES (%s, %s, %s, %s)",
            (store_name, username, email, password_hash),
        )
        conn.commit()
        user_id = cur.lastrowid
        cur.close()
        conn.close()

        session["user_id"] = user_id
        session["username"] = username
        session["store_name"] = store_name

        return jsonify({"message": "Account created successfully", "store_name": store_name}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "ID and password are required"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid ID or password"}), 401

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["store_name"] = user["store_name"]

        return jsonify({"message": "Login successful", "store_name": user["store_name"]}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@app.route("/api/session", methods=["GET"])
def check_session():
    if "user_id" in session:
        return jsonify({
            "logged_in": True,
            "username": session.get("username"),
            "store_name": session.get("store_name"),
        }), 200
    return jsonify({"logged_in": False}), 200


# ================== PRODUCTS ==================

@app.route("/api/products", methods=["GET"])
def get_products():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM products ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.get_json()
    sku = data.get("sku")
    name = data.get("name")
    price = data.get("price", 0)
    stock = data.get("stock", 0)

    if not sku or not name:
        return jsonify({"error": "sku and name are required"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (sku, name, price, stock) VALUES (%s, %s, %s, %s)",
            (sku, name, price, stock),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        conn.close()
        return jsonify({"id": new_id, "message": "Product added"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ================== CUSTOMERS ==================

@app.route("/api/customers", methods=["GET"])
def get_customers():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM customers ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/customers", methods=["POST"])
def add_customer():
    data = request.get_json()
    name = data.get("name")
    address = data.get("address", "")
    email = data.get("email", "")

    if not name:
        return jsonify({"error": "name is required"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO customers (name, address, email) VALUES (%s, %s, %s)",
            (name, address, email),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        conn.close()
        return jsonify({"id": new_id, "message": "Customer added"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ================== INVOICES ==================

@app.route("/api/invoices", methods=["GET"])
def get_invoices():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT i.*, c.name AS customer_name, c.address AS customer_address, c.email AS customer_email
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            ORDER BY i.id DESC
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/invoices/<int:invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT i.*, c.name AS customer_name, c.address AS customer_address, c.email AS customer_email
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.id = %s
            """,
            (invoice_id,),
        )
        invoice = cur.fetchone()
        if not invoice:
            cur.close()
            conn.close()
            return jsonify({"error": "Invoice not found"}), 404

        cur.execute("SELECT * FROM invoice_items WHERE invoice_id = %s", (invoice_id,))
        items = cur.fetchall()
        invoice["items"] = items

        cur.close()
        conn.close()
        return jsonify(invoice), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/invoices", methods=["POST"])
def create_invoice():
    """
    Sold-to, Ship-to, Invoice details, and Items are stored separately:
      - Sold-to  -> customers table (found or created here)
      - Ship-to  -> ship_name / ship_address columns on invoices
      - Invoice  -> invoices table
      - Items    -> invoice_items table

    Expected JSON body:
    {
      "invoice_no": "INV0000001",
      "customer_name": "John Doe",
      "customer_address": "...",
      "customer_email": "...",
      "ship_name": "...",
      "ship_address": "...",
      "invoice_date": "2026-07-02",
      "due_date": "2026-07-12",
      "terms": "NET 10",
      "order_no": "",
      "sales_rep": "",
      "tracking": "",
      "sub_total": 1000,
      "discount_pct": 0,
      "tax_pct": 10,
      "delivery_cost": 20,
      "invoice_total": 1120,
      "payments": 500,
      "amount_due": 620,
      "items": [
        {"sku": "111-222-331", "item_name": "Item 1", "qty": 1, "price": 100, "line_total": 100}
      ]
    }
    """
    data = request.get_json()
    items = data.get("items", [])

    if not data.get("invoice_no"):
        return jsonify({"error": "invoice_no is required"}), 400

    customer_name = data.get("customer_name")
    customer_email = data.get("customer_email")
    customer_address = data.get("customer_address")

    try:
        conn = get_connection()
        cur = conn.cursor()

        # ---- 1) SOLD TO: find existing customer by email, else create ----
        customer_id = None
        if customer_email:
            cur.execute("SELECT id FROM customers WHERE email = %s", (customer_email,))
            row = cur.fetchone()
            if row:
                customer_id = row[0]

        if customer_id is None and customer_name:
            cur.execute(
                "INSERT INTO customers (name, address, email) VALUES (%s, %s, %s)",
                (customer_name, customer_address, customer_email),
            )
            customer_id = cur.lastrowid

        # ---- 2) INVOICE + SHIP TO + STATUS + OTHER TABS ----
        cur.execute(
            """
            INSERT INTO invoices (
                invoice_no, customer_id, ship_name, ship_address,
                invoice_date, due_date, terms, order_no, sales_rep, tracking,
                sub_total, discount_pct, tax_pct, delivery_cost,
                invoice_total, payments, amount_due, status,
                printed_date, emailed_date, template,
                comments, private_comments, terms_conditions, footer_text, is_recurring
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                data.get("invoice_no"),
                customer_id,
                data.get("ship_name"),
                data.get("ship_address"),
                data.get("invoice_date") or datetime.now().date(),
                data.get("due_date") or None,
                data.get("terms"),
                data.get("order_no"),
                data.get("sales_rep"),
                data.get("tracking"),
                data.get("sub_total", 0),
                data.get("discount_pct", 0),
                data.get("tax_pct", 0),
                data.get("delivery_cost", 0),
                data.get("invoice_total", 0),
                data.get("payments", 0),
                data.get("amount_due", 0),
                "PAID" if float(data.get("amount_due", 0)) <= 0 else "UNPAID",
                data.get("printed_date") or None,
                data.get("emailed_date") or None,
                data.get("template"),
                data.get("comments"),
                data.get("private_comments"),
                data.get("terms_conditions"),
                data.get("footer_text"),
                bool(data.get("is_recurring", False)),
            ),
        )
        invoice_id = cur.lastrowid

        # ---- 3) ITEMS / PRICE ----
        total_qty_today = 0
        for item in items:
            qty = item.get("qty", 1)
            total_qty_today += qty
            cur.execute(
                """
                INSERT INTO invoice_items (invoice_id, sku, item_name, qty, price, line_total)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    invoice_id,
                    item.get("sku", ""),
                    item.get("item_name", ""),
                    qty,
                    item.get("price", 0),
                    item.get("line_total", 0),
                ),
            )

        # ---- 4) DAILY SUMMARY (Total Sales + Stock Sold, auto-updated) ----
        summary_date = data.get("invoice_date") or datetime.now().date()
        invoice_total = data.get("invoice_total", 0)
        cur.execute(
            """
            INSERT INTO daily_summary (summary_date, total_sales, stock_sold, stock_to_reorder)
            VALUES (%s, %s, %s, 0)
            ON DUPLICATE KEY UPDATE
                total_sales = total_sales + VALUES(total_sales),
                stock_sold = stock_sold + VALUES(stock_sold)
            """,
            (summary_date, invoice_total, total_qty_today),
        )

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"id": invoice_id, "customer_id": customer_id, "message": "Invoice saved successfully"}), 201

    except Error as e:
        return jsonify({"error": str(e)}), 500


# ================== DAILY SALES SUMMARY ==================

@app.route("/api/daily-summary/<summary_date>", methods=["GET"])
def get_daily_summary(summary_date):
    """summary_date format: YYYY-MM-DD"""
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM daily_summary WHERE summary_date = %s", (summary_date,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return jsonify({
                "summary_date": summary_date,
                "total_sales": 0,
                "stock_sold": 0,
                "stock_to_reorder": 0,
            }), 200
        return jsonify(row), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/daily-summary/<summary_date>", methods=["POST"])
def update_stock_to_reorder(summary_date):
    """
    Manually update the 'Stock to Reorder' value for a given date.
    Expected JSON body: { "stock_to_reorder": 25 }
    """
    data = request.get_json()
    stock_to_reorder = data.get("stock_to_reorder", 0)

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO daily_summary (summary_date, total_sales, stock_sold, stock_to_reorder)
            VALUES (%s, 0, 0, %s)
            ON DUPLICATE KEY UPDATE stock_to_reorder = VALUES(stock_to_reorder)
            """,
            (summary_date, stock_to_reorder),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Stock to reorder updated"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/daily-summary/<summary_date>/items", methods=["GET"])
def get_items_sold_on_date(summary_date):
    """
    Returns every line item sold on a given date (across all invoices),
    used by the Stock Sold drill-down page.
    """
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT ii.sku, ii.item_name, ii.qty, ii.price, ii.line_total,
                   i.invoice_no, i.invoice_date
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.invoice_date = %s
            ORDER BY i.id DESC
            """,
            (summary_date,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/invoices/<int:invoice_id>", methods=["DELETE"])
def delete_invoice(invoice_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM invoices WHERE id = %s", (invoice_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Invoice deleted"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)