🧾 Billing System Software

A complete full-stack invoicing and billing solution — built from scratch with HTML, CSS, JavaScript, Python (Flask), and MySQL. Designed to replace paper billing registers with a clean, database-backed invoicing workflow for small stores.


✨ Features


🔐 Secure Login & Registration — session-based authentication, every store gets its own account
🧾 Dynamic Invoice Generation — live Qty × Price calculations as you type
💰 Auto-computed Totals — discount, tax, delivery cost, and amount due calculated instantly
👤 Sold-to / Ship-to Management — customer records stored and reused across invoices
📦 Product Catalog Integration — add line items straight from a saved product list
📋 Status Tracking — printed/emailed dates, templates, and payment status per invoice
📝 Notes & Terms — comments, private notes, terms & conditions, and footer text saved per invoice
📊 Today's Sales Summary — live dashboard showing total sales and stock sold for the day
🔍 Stock Sold Drill-down — click into any day's sales to see every item sold, pulled straight from the database
🖨️ Clean Receipt Printing — one-click print view with just the shop name, items, total, and a signature line

🛠️ Tech Stack

LayerTechnologyFrontendHTML5, CSS3, JavaScriptBackendPython (Flask) — RESTful APIDatabaseMySQL — normalized relational schemaAuthFlask sessions + Werkzeug password hashing


📂 Project Structure

billing-system/
├── index.html            # Main invoice editor
├── login.html            # Login page
├── register.html         # Registration page
├── stock-details.html    # Stock sold drill-down report
├── style.css
├── script.js
└── backend/
    ├── app.py             # Flask app + REST API
    ├── config.example.py  # Copy to config.py and add your own credentials
    ├── schema.sql         # Database schema
    └── requirements.txt


🚀 Getting Started


Set up the database
Run backend/schema.sql in MySQL to create the database and tables.
Configure your credentials


bash   cp backend/config.example.py backend/config.py

Then edit backend/config.py with your own MySQL password and a random secret key.


Install dependencies


bash   cd backend
   pip install -r requirements.txt


Run the server


bash   python app.py


🔒 Security Note

backend/config.py is excluded from version control via .gitignore since it holds your database password and secret key. Never commit real credentials — always work off config.example.py.


🙋 About

Built as a hands-on full-stack project — from database design to frontend UX — to solve a real, practical business problem: giving a small store a proper digital billing system.

⭐ If you find this useful, consider starring the repo!
