-- ============================================
-- Departmental Store Billing System - Database
-- (Improved: Sold-to, Ship-to, Invoice, Items
--  are now cleanly separated into their own tables)
-- ============================================

CREATE DATABASE IF NOT EXISTS billing_system;
USE billing_system;

-- Drop old tables if re-running this fresh setup
DROP TABLE IF EXISTS invoice_items;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS daily_summary;
DROP TABLE IF EXISTS users;

-- ---------- 0) USERS (login / register) ----------
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    store_name VARCHAR(150) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(150),
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- 1) SOLD TO  (Customers) ----------
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    address TEXT,
    email VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Products (for "Add item from list") ----------
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL DEFAULT 0,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- 2) INVOICE + SHIP TO ----------
-- Ship-to details live here because they can be different
-- for every invoice (Sold-to customer stays fixed via customer_id,
-- Ship-to address is invoice-specific).
CREATE TABLE invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_no VARCHAR(50) UNIQUE NOT NULL,

    -- SOLD TO (link to customers table)
    customer_id INT,

    -- SHIP TO (kept separate from Sold-to)
    ship_name VARCHAR(150),
    ship_address TEXT,

    -- INVOICE fields
    invoice_date DATE,
    due_date DATE,
    terms VARCHAR(50),
    order_no VARCHAR(100),
    sales_rep VARCHAR(100),
    tracking VARCHAR(150),

    -- TOTALS
    sub_total DECIMAL(10,2) DEFAULT 0,
    discount_pct DECIMAL(5,2) DEFAULT 0,
    tax_pct DECIMAL(5,2) DEFAULT 0,
    delivery_cost DECIMAL(10,2) DEFAULT 0,
    invoice_total DECIMAL(10,2) DEFAULT 0,
    payments DECIMAL(10,2) DEFAULT 0,
    amount_due DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'UNPAID',

    -- STATUS TAB
    printed_date DATE,
    emailed_date DATE,
    template VARCHAR(100),

    -- OTHER TABS
    comments TEXT,
    private_comments TEXT,
    terms_conditions TEXT,
    footer_text TEXT,
    is_recurring BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- ---------- 3) ITEMS / PRICE (line items) ----------
CREATE TABLE invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    sku VARCHAR(50),
    item_name VARCHAR(200),
    qty INT NOT NULL DEFAULT 1,
    price DECIMAL(10,2) NOT NULL DEFAULT 0,
    line_total DECIMAL(10,2) NOT NULL DEFAULT 0,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

-- ---------- 4) DAILY SALES SUMMARY ----------
-- Total Sales and Stock Sold are updated automatically every time an
-- invoice is saved for that date. Stock to Reorder is entered manually
-- by the shop staff.
CREATE TABLE daily_summary (
    summary_date DATE PRIMARY KEY,
    total_sales DECIMAL(12,2) NOT NULL DEFAULT 0,
    stock_sold INT NOT NULL DEFAULT 0,
    stock_to_reorder INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ---------- Sample data ----------
INSERT INTO products (sku, name, price, stock) VALUES
('111-222-331', 'Demo live item name 1', 100.00, 50),
('111-222-332', 'Demo live item name 2', 200.00, 30),
('111-222-333', 'Demo live item name 3', 700.00, 15);

INSERT INTO customers (name, address, email) VALUES
('John Doe', '1234 Any street, Anytown, 55555', 'johndoe@anyhostname.com');