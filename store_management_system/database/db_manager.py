"""
SQLite Database Engine and Secure Authentication Manager.
Provides persistent ACID-compliant relational storage, secure PBKDF2-HMAC-SHA256
password hashing, user management, and transactional query execution.
"""

import hashlib
import os
import secrets
import sqlite3
import threading
from datetime import datetime, date
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from typing import Any, Dict, List, Optional, Tuple

from config import DB_PATH
from utils.logger import get_logger

logger = get_logger("DBManager")


def hash_password(password: str, salt_hex: Optional[str] = None) -> Tuple[str, str]:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Returns (hex_hash, hex_salt).
    """
    if salt_hex is None:
        salt_bytes = secrets.token_bytes(16)
        salt_hex = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt_hex)

    derived = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password.encode("utf-8"),
        salt=salt_bytes,
        iterations=100_000
    )
    return derived.hex(), salt_hex


def verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    """Verifies a password against the stored PBKDF2 hash using constant-time comparison."""
    calculated_hash, _ = hash_password(password, salt_hex)
    return secrets.compare_digest(calculated_hash, stored_hash)


class DatabaseManager:
    """
    Thread-safe SQLite database manager for Store Management System.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Creates a connection with Row factory and WAL mode."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_database(self) -> None:
        """Initializes tables and seeds default users if not present."""
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 1. Users Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        full_name TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'Cashier',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 2. Categories Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        category_id TEXT PRIMARY KEY,
                        category_name TEXT UNIQUE NOT NULL,
                        description TEXT
                    );
                """)

                # 3. Suppliers Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS suppliers (
                        supplier_id TEXT PRIMARY KEY,
                        supplier_name TEXT NOT NULL,
                        contact_person TEXT,
                        email TEXT,
                        phone TEXT,
                        address TEXT
                    );
                """)

                # 4. Customers Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS customers (
                        customer_id TEXT PRIMARY KEY,
                        customer_name TEXT NOT NULL,
                        email TEXT,
                        phone TEXT,
                        city TEXT,
                        registration_date TEXT
                    );
                """)

                # 5. Products Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        product_id TEXT PRIMARY KEY,
                        sku TEXT UNIQUE NOT NULL,
                        product_name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        brand TEXT NOT NULL,
                        purchase_price REAL NOT NULL,
                        selling_price REAL NOT NULL,
                        quantity INTEGER NOT NULL,
                        supplier TEXT NOT NULL,
                        expiry_date TEXT,
                        description TEXT,
                        image_path TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 6. Sales Transactions Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sales (
                        sale_id TEXT PRIMARY KEY,
                        product_id TEXT,
                        product_name TEXT,
                        quantity_sold INTEGER NOT NULL,
                        unit_price REAL NOT NULL,
                        total_amount REAL NOT NULL,
                        sale_date TEXT NOT NULL,
                        payment_method TEXT NOT NULL,
                        customer_id TEXT
                    );
                """)

                # 7. Sale Items Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sale_items (
                        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sale_id TEXT,
                        product_id TEXT,
                        quantity INTEGER,
                        unit_price REAL,
                        subtotal REAL,
                        FOREIGN KEY(sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
                        FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE SET NULL
                    );
                """)

                conn.commit()

            # Seed default users
            self._seed_default_users()

    def _seed_default_users(self) -> None:
        """Seeds default administrator and cashier accounts if database has no users."""
        default_users = [
            ("admin", "admin@supermarket.com", "admin123", "Store Administrator", "Super Admin"),
            ("cashier", "cashier@supermarket.com", "cashier123", "Sarah Miller", "Senior Cashier"),
            ("manager", "manager@supermarket.com", "manager123", "David Clark", "Inventory Manager")
        ]

        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for username, email, pwd, full_name, role in default_users:
                    cursor.execute("SELECT user_id FROM users WHERE username = ? OR email = ?", (username, email))
                    if not cursor.fetchone():
                        p_hash, salt = hash_password(pwd)
                        cursor.execute("""
                            INSERT INTO users (username, email, password_hash, salt, full_name, role)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (username, email, p_hash, salt, full_name, role))
                conn.commit()

    # =========================================================================
    # AUTHENTICATION METHODS
    # =========================================================================

    def authenticate_user(self, username_or_email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticates a user by username or email.
        Returns (success, message, user_dict).
        """
        identifier = username_or_email.strip().lower()
        if not identifier or not password:
            return False, "Username/Email and Password are required.", None

        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, username, email, password_hash, salt, full_name, role, created_at
                    FROM users
                    WHERE lower(username) = ? OR lower(email) = ?
                """, (identifier, identifier))
                row = cursor.fetchone()

                if not row:
                    return False, "Invalid username or password.", None

                if verify_password(password, row["password_hash"], row["salt"]):
                    user_dict = {
                        "user_id": row["user_id"],
                        "username": row["username"],
                        "email": row["email"],
                        "name": row["full_name"],
                        "role": row["role"],
                        "created_at": row["created_at"]
                    }
                    logger.info(f"User '{row['username']}' authenticated successfully.")
                    return True, "Authentication successful.", user_dict
                else:
                    return False, "Invalid username or password.", None

    def register_user(
        self,
        full_name: str,
        email: str,
        username: str,
        password: str,
        role: str = "Cashier"
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Registers a new user with password validation and duplicate check.
        """
        full_name = full_name.strip()
        email = email.strip().lower()
        username = username.strip().lower()

        if not full_name:
            return False, "Full Name cannot be empty.", None
        if not email or "@" not in email:
            return False, "Please enter a valid email address.", None
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long.", None
        if len(password) < 6:
            return False, "Password must be at least 6 characters long.", None

        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Check duplicate username
                cursor.execute("SELECT user_id FROM users WHERE lower(username) = ?", (username,))
                if cursor.fetchone():
                    return False, f"Username '{username}' is already taken. Please choose another.", None

                # Check duplicate email
                cursor.execute("SELECT user_id FROM users WHERE lower(email) = ?", (email,))
                if cursor.fetchone():
                    return False, f"Email '{email}' is already registered. Please login.", None

                p_hash, salt = hash_password(password)
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, salt, full_name, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, email, p_hash, salt, full_name, role))
                user_id = cursor.lastrowid
                conn.commit()

                user_dict = {
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "name": full_name,
                    "role": role
                }
                logger.info(f"Registered new user '{username}' (ID: {user_id}).")
                return True, "Account created successfully!", user_dict

    def reset_password(self, email_or_username: str, new_password: str) -> Tuple[bool, str]:
        """Resets user password with hashing."""
        identifier = email_or_username.strip().lower()
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters long."

        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM users WHERE lower(username) = ? OR lower(email) = ?", (identifier, identifier))
                row = cursor.fetchone()
                if not row:
                    return False, "Account with that username or email does not exist."

                p_hash, salt = hash_password(new_password)
                cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE user_id = ?", (p_hash, salt, row["user_id"]))
                conn.commit()
                return True, "Password has been reset successfully. You can now login."

