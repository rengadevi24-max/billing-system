import os

# ---- MySQL connection settings ----
# Change these to match your local MySQL setup (XAMPP / WAMP / MySQL Workbench etc.)
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "renga@24"),   # put your MySQL root password here
    "database": os.environ.get("DB_NAME", "billing_system"),
}

# ---- Session secret key (used to keep users logged in) ----
# You can change this to any random string.
SECRET_KEY = os.environ.get("SECRET_KEY", "billing-system-secret-key-change-me")