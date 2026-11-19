"""
CSV Handler and Data Science Dataset Generator for Store Management System.
Handles atomic file I/O, schema enforcement, reproducible 100+ product dataset generation,
and synchronization with the persistent SQLite database engine.
"""

import os
import random
import uuid
from datetime import date, datetime, timedelta
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from config import (
    DATA_DIR,
    PRODUCTS_FILE,
    SUPPLIERS_FILE,
    SALES_FILE,
    CUSTOMERS_FILE,
    STOCK_MOVEMENTS_FILE,
    EXPIRY_ALERTS_FILE,
    EXPIRY_CRITICAL_DAYS,
    EXPIRY_WARNING_DAYS,
    EXPIRY_CAUTION_DAYS,
)
from utils.logger import get_logger

logger = get_logger("CSVHandler")

# Master Schema Definitions
SCHEMAS = {
    "products": [
        "product_id",
        "sku",
        "product_name",
        "category",
        "brand",
        "purchase_price",
        "selling_price",
        "stock_quantity",
        "quantity",
        "supplier_id",
        "supplier",
        "minimum_stock",
        "expiry_date",
        "description",
    ],
    "suppliers": [
        "supplier_id",
        "supplier_name",
        "contact_person",
        "email",
        "phone",
        "address",
    ],
    "sales": [
        "sale_id",
        "transaction_id",
        "product_id",
        "product_name",
        "quantity_sold",
        "quantity",
        "unit_price",
        "total_amount",
        "sale_date",
        "payment_method",
        "customer_id",
    ],
    "customers": [
        "customer_id",
        "customer_name",
        "email",
        "phone",
        "city",
        "registration_date",
    ],
    "stock_movements": [
        "movement_id",
        "product_id",
        "movement_type",
        "quantity_change",
        "movement_date",
        "notes",
        "remarks",
    ],
    "expiry_alerts": [
        "alert_id",
        "product_id",
        "product_name",
        "category",
        "batch_number",
        "expiry_date",
        "quantity_affected",
        "days_until_expiry",
        "alert_status",
        "notification_sent",
        "acknowledged",
    ],
    "sms_logs": [
        "sms_id",
        "timestamp",
        "recipient_phone",
        "recipient_name",
        "message_type",
        "message_body",
        "gateway",
        "status",
        "delivery_id",
    ],
}


def read_csv_safe(file_path: Path, expected_columns: List[str]) -> pd.DataFrame:
    """Reads a CSV file safely with schema reconciliation and fallback."""
    file_path = Path(file_path)
    if not file_path.exists() or file_path.stat().st_size == 0:
        return pd.DataFrame(columns=expected_columns)
    try:
        df = pd.read_csv(file_path, dtype=str)
        # Column name mapping for legacy and alternate schema compatibility
        col_aliases = {
            "supplier_id": "supplier",
            "supplier": "supplier_id",
            "stock_quantity": "quantity",
            "quantity": "stock_quantity",
            "contact_number": "phone",
            "phone": "contact_number",
            "transaction_id": "sale_id",
        }
        for c1, c2 in col_aliases.items():
            if c1 in df.columns and c2 not in df.columns:
                df[c2] = df[c1]
            elif c2 in df.columns and c1 not in df.columns:
                df[c1] = df[c2]

        for col in expected_columns:
            if col not in df.columns:
                df[col] = ""

        # Provide common UI compatibility aliases
        if "contact_number" not in df.columns and "phone" in df.columns:
            df["contact_number"] = df["phone"]
        if "product_category" not in df.columns and "supplier_id" in df.columns:
            df["product_category"] = "General Goods"

        return df
    except Exception as e:
        logger.error(f"Error reading {file_path.name}: {e}")
        return pd.DataFrame(columns=expected_columns)


def write_csv_atomic(arg1: Any, arg2: Any) -> bool:
    """
    Writes a DataFrame to disk atomically using a temporary file.
    Accepts arguments in either order: (file_path, df) or (df, file_path).
    Returns True on success, False on failure.
    """
    if isinstance(arg1, pd.DataFrame):
        df, file_path = arg1, Path(arg2)
    else:
        file_path, df = Path(arg1), arg2

    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_file = file_path.with_suffix(f".tmp_{os.getpid()}_{uuid.uuid4().hex[:6]}")
    try:
        df.to_csv(temp_file, index=False)
        os.replace(temp_file, file_path)
        return True
    except Exception as e:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass
        logger.error(f"Failed to write atomic CSV to {file_path.name}: {e}")
        return False


def classify_alert_status(days_until: int) -> str:
    """Classifies expiry risk level based on configured day thresholds."""
    if days_until <= EXPIRY_CRITICAL_DAYS:
        return "EXPIRED"
    elif days_until <= EXPIRY_WARNING_DAYS:
        return "CRITICAL"
    elif days_until <= EXPIRY_CAUTION_DAYS:
        return "WARNING"
    return "SAFE"


def generate_synthetic_datasets(target_data_dir: Optional[Path] = None, force_regenerate: bool = False) -> None:
    """
    Generates reproducible, internally consistent Enterprise Supermarket datasets:
    - 100+ Products across Groceries, Beverages, Dairy, Snacks, Personal Care, Household, Electronics
    - 15 Suppliers
    - 40 Customers
    - 150+ Sales Transactions
    - Reconciled Stock Movements & Expiry Alerts
    """
    data_dir = Path(target_data_dir) if target_data_dir else DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    products_file = data_dir / "products.csv"
    suppliers_file = data_dir / "suppliers.csv"
    sales_file = data_dir / "sales.csv"
    customers_file = data_dir / "customers.csv"
    stock_movements_file = data_dir / "stock_movements.csv"
    expiry_alerts_file = data_dir / "expiry_alerts.csv"

    # Skip if files already exist unless forced
    files_exist = all(p.exists() and p.stat().st_size > 0 for p in [products_file, suppliers_file, sales_file])
    if files_exist and not force_regenerate:
        logger.info(f"Synthetic datasets already exist in {data_dir.name}. Skipping generation.")
        return

    logger.info(f"Generating 100+ product enterprise dataset in {data_dir}...")
    random.seed(42)
    np.random.seed(42)
    today = date.today()

    # 1. SUPPLIERS (15 realistic companies)
    suppliers_data = [
        ("SUP-001", "Apex Beverage Distributors", "Marcus Vance", "orders@apexbeverage.com", "+1-555-0101", "101 Industrial Pkwy, Seattle, WA"),
        ("SUP-002", "Golden Dairy Farms Co.", "Elena Rossi", "contact@goldendairy.com", "+1-555-0102", "240 Farmview Rd, Madison, WI"),
        ("SUP-003", "Artisan Hearth Bakery Supplies", "Thomas Baker", "sales@artisanhearth.com", "+1-555-0103", "55 Flour Mill Way, Portland, OR"),
        ("SUP-004", "Valley Harvest Organics", "Rachel Green", "supply@valleyharvest.org", "+1-555-0104", "780 Orchard Ln, Fresno, CA"),
        ("SUP-005", "Global Pantry Imports LLC", "Kenji Sato", "info@globalpantry.com", "+1-555-0105", "400 Harbor Blvd, Long Beach, CA"),
        ("SUP-006", "PureBotanicals Personal Care", "Chloe Bennett", "wholesale@purebotanicals.com", "+1-555-0106", "12 Wellness Dr, Denver, CO"),
        ("SUP-007", "SweetTreats Confectionery", "Arthur Pendelton", "orders@sweettreats.net", "+1-555-0107", "88 Cocoa Plaza, Hershey, PA"),
        ("SUP-008", "Vitality Health & Nutrition", "Dr. Samantha Reed", "sales@vitalityhealth.com", "+1-555-0108", "300 BioPark Blvd, Austin, TX"),
        ("SUP-009", "Cascade Frozen Foods Ltd", "Brian O'Connor", "logistics@cascadefrozen.com", "+1-555-0109", "92 Glacier Way, Boise, ID"),
        ("SUP-010", "Heritage Grain & Spice Co.", "Amara Okafor", "contact@heritagegrain.com", "+1-555-0110", "64 Meadow Brook Rd, Omaha, NE"),
        ("SUP-011", "Nordic Seafood & Deli", "Lars Lindqvist", "accounts@nordicseafood.com", "+1-555-0111", "15 Pier 4, Boston, MA"),
        ("SUP-012", "GreenLife Eco Household", "Maya Lin", "support@greenlifeeco.com", "+1-555-0112", "500 Recycle Ave, Minneapolis, MN"),
        ("SUP-013", "TechNest Electronics Direct", "Vikram Patel", "b2b@technest.com", "+1-555-0113", "120 Silicon Ave, San Jose, CA"),
        ("SUP-014", "SunGlade Citrus & Fruits", "Diego Morales", "sales@sunglade.com", "+1-555-0114", "850 Grove Rd, Orlando, FL"),
        ("SUP-015", "PrimeCut Ranchers Co-Op", "Caleb Jackson", "dispatch@primecutranch.com", "+1-555-0115", "310 Cattleman Trail, Fort Worth, TX"),
    ]
    df_suppliers = pd.DataFrame(suppliers_data, columns=SCHEMAS["suppliers"])
    write_csv_atomic(df_suppliers, suppliers_file)

    # 2. CUSTOMERS (40 realistic supermarket shoppers)
    first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth",
                   "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin"]

    customers_data = []
    for cid in range(1, 41):
        fn = first_names[cid % len(first_names)]
        ln = last_names[(cid * 3) % len(last_names)]
        c_name = f"{fn} {ln}"
        c_email = f"{fn.lower()}.{ln.lower()}{cid}@example.com"
        c_phone = f"+1-555-{cid:04d}"
        c_city = cities[cid % len(cities)]
        reg_date = (today - timedelta(days=cid * 7)).strftime("%Y-%m-%d")
        customers_data.append((f"CUST-{cid:04d}", c_name, c_email, c_phone, c_city, reg_date))

    df_customers = pd.DataFrame(customers_data, columns=SCHEMAS["customers"])
    write_csv_atomic(df_customers, customers_file)

    # 3. 100+ REALISTIC PRODUCTS (Groceries, Beverages, Dairy, Snacks, Personal Care, Household, Electronics)
    catalog_templates = [
        # Beverages
        ("Organic Arabica Dark Roast Coffee 1lb", "Beverages", "RoastCraft", 6.50, 12.99, "SUP-001", 120),
        ("Sparkling Spring Water 500ml 12pk", "Beverages", "PureSpring", 4.20, 8.49, "SUP-001", 365),
        ("Cold Brew Black Coffee Can 250ml", "Beverages", "RoastCraft", 1.40, 2.99, "SUP-001", 45),
        ("Matcha Green Tea Extract 100g", "Beverages", "ZenTea", 9.00, 17.50, "SUP-001", 180),
        ("Kombucha Ginger Lemon Organic 16oz", "Beverages", "WildBrew", 2.20, 4.29, "SUP-001", 60),
        ("Fresh Pressed Orange Juice 64oz", "Beverages", "SunGlade", 3.00, 5.79, "SUP-014", 12),
        ("Almond Milk Unsweetened 64oz", "Beverages", "NutriSilk", 2.10, 3.99, "SUP-001", 45),
        ("Pure Coconut Water 1 Liter", "Beverages", "TropiPure", 2.50, 4.89, "SUP-001", 200),
        ("Earl Grey Loose Leaf Black Tea 8oz", "Beverages", "ZenTea", 4.80, 9.50, "SUP-001", 300),
        ("Sparkling Lime Seltzer 12oz 8pk", "Beverages", "PureSpring", 2.80, 5.49, "SUP-001", 240),
        ("Electrolyte Hydration Drink 20oz", "Beverages", "HydroFuel", 1.20, 2.49, "SUP-008", 180),
        ("Organic Cranberry Juice 32oz", "Beverages", "SunGlade", 2.90, 5.29, "SUP-014", 90),
        ("Chai Tea Spiced Latte Concentrate 32oz", "Beverages", "ZenTea", 3.40, 6.49, "SUP-001", 110),
        ("Sparkling Apple Cider 750ml", "Beverages", "SunGlade", 2.60, 4.99, "SUP-014", 365),
        ("Zero Sugar Lemonade 52oz", "Beverages", "SunGlade", 1.80, 3.69, "SUP-014", 30),

        # Dairy & Eggs
        ("Whole Milk Grass-Fed 1 Gallon", "Dairy", "Golden Dairy", 2.60, 4.89, "SUP-002", 5),
        ("Pasture-Raised Grade A Large Eggs 12pk", "Dairy", "Golden Dairy", 3.10, 5.99, "SUP-002", 14),
        ("Greek Yogurt Plain 32oz", "Dairy", "Golden Dairy", 2.80, 5.49, "SUP-002", 6),
        ("Aged Sharp Cheddar Cheese Block 8oz", "Dairy", "Golden Dairy", 3.20, 6.25, "SUP-002", 60),
        ("Salted Sweet Cream Butter 16oz", "Dairy", "Golden Dairy", 2.90, 5.79, "SUP-002", 40),
        ("Organic Cottage Cheese 16oz", "Dairy", "Golden Dairy", 2.30, 4.49, "SUP-002", 10),
        ("Fresh Mozzarella Ball in Water 8oz", "Dairy", "Golden Dairy", 2.70, 5.19, "SUP-002", 12),
        ("Heavy Whipping Cream 16oz", "Dairy", "Golden Dairy", 1.90, 3.89, "SUP-002", 8),
        ("Shredded Parmesan Cheese 6oz", "Dairy", "Golden Dairy", 2.40, 4.79, "SUP-002", 90),
        ("Sour Cream All Natural 16oz", "Dairy", "Golden Dairy", 1.50, 2.99, "SUP-002", 15),
        ("Oat Milk Extra Creamy 64oz", "Dairy", "NutriSilk", 2.40, 4.69, "SUP-002", 35),
        ("Smoked Gouda Slices 7oz", "Dairy", "Golden Dairy", 3.00, 5.89, "SUP-002", 45),
        ("Strawberry Kefir Cultured Drink 32oz", "Dairy", "Golden Dairy", 2.60, 4.99, "SUP-002", 14),
        ("Organic Cream Cheese Block 8oz", "Dairy", "Golden Dairy", 1.80, 3.49, "SUP-002", 30),
        ("Swiss Cheese Slices Deli Cut 8oz", "Dairy", "Golden Dairy", 2.80, 5.49, "SUP-002", 28),

        # Groceries & Pantry
        ("Artisan Sourdough Boule 500g", "Groceries", "Artisan Hearth", 2.10, 4.99, "SUP-003", -2),
        ("Multi-Grain Sandwich Bread 20oz", "Groceries", "Artisan Hearth", 1.80, 3.79, "SUP-003", 4),
        ("Brioche Burger Buns 6pk", "Groceries", "Artisan Hearth", 2.20, 4.49, "SUP-003", 8),
        ("Organic Honey Crisp Apples 3lb Bag", "Groceries", "Valley Harvest", 3.50, 6.99, "SUP-004", 18),
        ("Baby Spinach Salad Tub 16oz", "Groceries", "Valley Harvest", 2.00, 4.29, "SUP-004", -1),
        ("Organic Hass Avocados 4pk", "Groceries", "Valley Harvest", 2.90, 5.79, "SUP-004", 10),
        ("Extra Virgin Olive Oil Cold Pressed 750ml", "Groceries", "Global Pantry", 7.50, 14.99, "SUP-005", 300),
        ("Basmati Rice Aged Reserve 5lb", "Groceries", "Global Pantry", 5.20, 10.49, "SUP-005", 450),
        ("Organic Whole Peeled Tomatoes 28oz", "Groceries", "Global Pantry", 1.60, 3.29, "SUP-005", 400),
        ("Stone Ground Whole Wheat Flour 5lb", "Groceries", "Heritage Grain", 3.10, 6.49, "SUP-010", 240),
        ("Organic Rolled Oats Tub 42oz", "Groceries", "Heritage Grain", 2.70, 5.89, "SUP-010", 270),
        ("Pure Maple Syrup Grade A 12oz", "Groceries", "Global Pantry", 5.80, 10.99, "SUP-005", 365),
        ("Italian Penne Rigate Pasta 16oz", "Groceries", "Global Pantry", 1.10, 2.29, "SUP-005", 500),
        ("Organic Black Beans Can 15oz", "Groceries", "Global Pantry", 0.70, 1.49, "SUP-005", 600),
        ("Organic Quinoa Grain 2lb", "Groceries", "Heritage Grain", 3.90, 7.89, "SUP-010", 300),
        ("Wildflower Raw Honey 16oz", "Groceries", "Global Pantry", 4.50, 8.99, "SUP-005", 400),
        ("Peanut Butter Creamy Natural 16oz", "Groceries", "Global Pantry", 2.30, 4.69, "SUP-005", 180),
        ("Organic Tomato Basil Pasta Sauce 24oz", "Groceries", "Global Pantry", 2.40, 4.99, "SUP-005", 270),
        ("Pink Himalayan Sea Salt Grinder 6oz", "Groceries", "Heritage Grain", 2.10, 4.49, "SUP-010", 700),
        ("Organic Chia Seeds 12oz", "Groceries", "Heritage Grain", 3.20, 6.49, "SUP-010", 350),

        # Snacks & Confectionery
        ("Dark Chocolate Almond Bark 7oz", "Snacks", "SweetTreats", 2.40, 5.19, "SUP-007", 150),
        ("Kettle Cooked Sea Salt Chips 8oz", "Snacks", "CrispCraze", 1.70, 3.99, "SUP-007", 90),
        ("Gourmet Roasted Pistachios Salted 12oz", "Snacks", "NutriCrunch", 4.80, 9.89, "SUP-007", 180),
        ("Organic Gummy Bears Gelatin Free 6oz", "Snacks", "SweetTreats", 1.50, 3.29, "SUP-007", 120),
        ("Artisan Pita Chips Garlic & Herb 9oz", "Snacks", "CrispCraze", 2.10, 4.49, "SUP-007", 90),
        ("Cacao Nib Granola Bar 5pk", "Snacks", "NutriCrunch", 2.60, 5.29, "SUP-007", 110),
        ("Roasted Cashews Lightly Salted 10oz", "Snacks", "NutriCrunch", 4.20, 8.79, "SUP-007", 180),
        ("Organic White Cheddar Popcorn 5oz", "Snacks", "CrispCraze", 1.60, 3.49, "SUP-007", 75),
        ("Pretzel Crisps Original 7.2oz", "Snacks", "CrispCraze", 1.80, 3.79, "SUP-007", 120),
        ("Milk Chocolate Truffle Box 8oz", "Snacks", "SweetTreats", 4.90, 9.99, "SUP-007", 180),
        ("Spicy Jalapeno Tortilla Chips 11oz", "Snacks", "CrispCraze", 2.00, 4.19, "SUP-007", 90),
        ("Sea Salt Caramel Rice Cakes 6.5oz", "Snacks", "NutriCrunch", 1.40, 2.99, "SUP-007", 100),
        ("Trail Mix Cranberry Almond 16oz", "Snacks", "NutriCrunch", 3.80, 7.99, "SUP-007", 150),
        ("Peanut Butter Cups Dark Chocolate 4pk", "Snacks", "SweetTreats", 1.60, 3.49, "SUP-007", 90),
        ("Fruit Leather Snack Strips 12pk", "Snacks", "SweetTreats", 3.00, 6.29, "SUP-007", 120),

        # Personal Care
        ("Natural Tea Tree Shampoo 16oz", "Personal Care", "PureBotanicals", 4.50, 9.99, "SUP-006", 600),
        ("Moisturizing Shea Butter Body Lotion 12oz", "Personal Care", "PureBotanicals", 5.00, 11.49, "SUP-006", 500),
        ("Gentle Hydrating Facial Cleanser 8oz", "Personal Care", "PureBotanicals", 6.20, 13.99, "SUP-006", 480),
        ("Mineral Sunscreen SPF 50 Broad Spectrum 5oz", "Personal Care", "SunGuard", 6.50, 14.50, "SUP-006", 400),
        ("Organic Spearmint Toothpaste 4.5oz", "Personal Care", "DentFresh", 2.40, 5.29, "SUP-006", 450),
        ("Natural Deodorant Stick Lavender 2.6oz", "Personal Care", "PureBotanicals", 4.10, 8.99, "SUP-006", 365),
        ("Argan Oil Hair Treatment Mask 8oz", "Personal Care", "PureBotanicals", 7.00, 15.99, "SUP-006", 550),
        ("Charcoal Bamboo Toothbrush 4pk", "Personal Care", "DentFresh", 2.50, 5.99, "SUP-006", 700),
        ("Hydrating Aloe Vera Gel 12oz", "Personal Care", "PureBotanicals", 3.20, 6.99, "SUP-006", 450),
        ("Rosewater Facial Mist Toner 4oz", "Personal Care", "PureBotanicals", 4.80, 10.50, "SUP-006", 380),
        ("Coconut Milk Bar Soap 3pk", "Personal Care", "PureBotanicals", 2.70, 5.99, "SUP-006", 500),
        ("Lip Balm Organic Beeswax 3pk", "Personal Care", "PureBotanicals", 2.00, 4.49, "SUP-006", 365),
        ("Epsom Salt Lavender Bath Soak 3lb", "Personal Care", "PureBotanicals", 3.60, 7.99, "SUP-006", 600),
        ("Micellar Cleansing Water 13oz", "Personal Care", "PureBotanicals", 4.00, 8.89, "SUP-006", 420),
        ("Hand Cream Rich Shea 3.4oz", "Personal Care", "PureBotanicals", 3.10, 6.79, "SUP-006", 365),

        # Household & Cleaning
        ("Plant-Based Dish Soap Citrus 25oz", "Household", "GreenLife", 2.20, 4.79, "SUP-012", 500),
        ("Eco Laundry Detergent Sheets 60 loads", "Household", "GreenLife", 7.00, 14.99, "SUP-012", 600),
        ("Multi-Surface Cleaning Spray 28oz", "Household", "GreenLife", 2.40, 5.29, "SUP-012", 450),
        ("Recycled Paper Towels 6 Jumbo Rolls", "Household", "GreenLife", 5.50, 11.49, "SUP-012", 700),
        ("Bamboo Kitchen Scrub Brushes 3pk", "Household", "GreenLife", 3.20, 6.99, "SUP-012", 800),
        ("Compostable Trash Bags 13 Gallon 30ct", "Household", "GreenLife", 4.80, 9.99, "SUP-012", 600),
        ("Baking Soda Natural Deodorizer 16oz", "Household", "GreenLife", 0.90, 1.99, "SUP-012", 900),
        ("Microfiber Cleaning Cloths 8pk", "Household", "GreenLife", 4.00, 8.49, "SUP-012", 800),
        ("Non-Toxic Bathroom Cleaner Spray 24oz", "Household", "GreenLife", 2.60, 5.69, "SUP-012", 500),
        ("Wool Dryer Balls Reusable 6pk", "Household", "GreenLife", 6.00, 12.99, "SUP-012", 1000),
        ("Hypoallergenic Fabric Softener 64oz", "Household", "GreenLife", 3.80, 7.99, "SUP-012", 500),
        ("Stainless Steel Straw Set with Brush 4pk", "Household", "GreenLife", 2.80, 6.29, "SUP-012", 900),
        ("Beeswax Food Wraps Assorted 3pk", "Household", "GreenLife", 7.50, 15.99, "SUP-012", 600),
        ("Natural Air Freshener Spray Eucalyptus 8oz", "Household", "GreenLife", 3.00, 6.49, "SUP-012", 400),
        ("Cellulose Sponge Cloths 4pk", "Household", "GreenLife", 2.50, 5.49, "SUP-012", 700),

        # Electronics & POS Accessories
        ("USB-C Fast Charging Cable Braided 6ft", "Electronics", "TechNest", 3.50, 9.99, "SUP-013", 1000),
        ("Bluetooth Compact Speaker Water Resistant", "Electronics", "TechNest", 14.00, 29.99, "SUP-013", 1000),
        ("Wireless Optical Mouse Ergonomic", "Electronics", "TechNest", 6.50, 14.99, "SUP-013", 1000),
        ("Thermal Receipt Paper Rolls 80mm 10pk", "Electronics", "TechNest", 8.00, 16.50, "SUP-013", 1000),
        ("Barcode Scanner USB Laser Handheld", "Electronics", "TechNest", 18.00, 39.99, "SUP-013", 1000),
        ("Dual Port USB-C Wall Charger 30W", "Electronics", "TechNest", 7.20, 16.99, "SUP-013", 1000),
        ("Rechargeable AA Batteries NiMH 4pk", "Electronics", "TechNest", 5.00, 11.99, "SUP-013", 900),
        ("Noise-Isolating Earbuds with Mic", "Electronics", "TechNest", 8.50, 18.99, "SUP-013", 1000),
        ("Portable Power Bank 10000mAh Slim", "Electronics", "TechNest", 11.00, 24.99, "SUP-013", 1000),
        ("LED Desk Lamp with Wireless Charging Pad", "Electronics", "TechNest", 15.00, 34.99, "SUP-013", 1000),
    ]

    products_data = []
    movements_data = []
    alerts_data = []

    for idx, (p_name, cat, brand, p_cost, s_price, supp_id, days_exp) in enumerate(catalog_templates, start=1):
        pid = f"PRD-{idx:04d}"
        sku = f"SKU-{cat[:3].upper()}-{idx:04d}"
        base_stock = random.randint(25, 120)
        exp_date_str = (today + timedelta(days=days_exp)).strftime("%Y-%m-%d")

        products_data.append((
            pid,
            sku,
            p_name,
            cat,
            brand,
            f"{p_cost:.2f}",
            f"{s_price:.2f}",
            str(base_stock),
            str(base_stock),
            supp_id,
            supp_id,
            "10",
            exp_date_str,
            f"{brand} {p_name}"
        ))

        # Stock Movement: Initial Stock
        movements_data.append((
            f"MOV-{idx:04d}", pid, "INITIAL_STOCK", str(base_stock), today.strftime("%Y-%m-%d"), "Baseline dataset generation", "Baseline dataset generation"
        ))

        # Expiry Alert
        alert_status = classify_alert_status(days_exp)
        notif_sent = "Sent" if alert_status in ["EXPIRED", "EXPIRING_SOON_7"] else "Pending"
        batch_no = f"BCH-{abs(hash(pid)) % 9000 + 1000}"
        alerts_data.append((
            f"ALT-{idx:04d}",
            pid,
            p_name,
            cat,
            batch_no,
            exp_date_str,
            str(base_stock),
            str(days_exp),
            alert_status,
            notif_sent,
            "False"
        ))

    df_products = pd.DataFrame(products_data, columns=SCHEMAS["products"])
    write_csv_atomic(df_products, products_file)

    df_movements = pd.DataFrame(movements_data, columns=SCHEMAS["stock_movements"])
    write_csv_atomic(df_movements, stock_movements_file)

    df_alerts = pd.DataFrame(alerts_data, columns=SCHEMAS["expiry_alerts"])
    write_csv_atomic(df_alerts, expiry_alerts_file)

    # 4. 150+ SALES TRANSACTIONS
    sales_data = []
    payment_methods = ["Credit Card", "Cash", "Mobile Pay", "Debit Card"]

    # Generate 160 realistic transactions across past 60 days
    txn_id = 1001
    for i in range(160):
        prod_idx = i % len(products_data)
        p_row = products_data[prod_idx]
        pid, p_name, s_price = p_row[0], p_row[2], float(p_row[6])

        qty_sold = random.choices([1, 2, 3, 4, 5], weights=[45, 30, 15, 7, 3])[0]
        tot_amount = round(qty_sold * s_price, 2)
        days_back = int(60 * (1 - (i / 160.0)))
        s_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
        pay_method = payment_methods[i % len(payment_methods)]

        sales_data.append((
            f"TXN-{txn_id}", f"TXN-{txn_id}", pid, p_name, str(qty_sold), str(qty_sold), f"{s_price:.2f}", f"{tot_amount:.2f}", s_date, pay_method, f"CUST-{((i % 40) + 1):04d}"
        ))
        txn_id += 1

    df_sales = pd.DataFrame(sales_data, columns=SCHEMAS["sales"])
    write_csv_atomic(df_sales, sales_file)

    logger.info(f"Successfully generated {len(products_data)} products, {len(suppliers_data)} suppliers, {len(customers_data)} customers, and {len(sales_data)} sales transactions.")
