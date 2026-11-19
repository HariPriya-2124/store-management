# Store Management System Using Python for Data Science
**Enterprise Desktop POS, Inventory Control, Expiry Monitoring, and Business Intelligence System**

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-Tkinter%20%2F%20ttk-0F172A.svg)](https://docs.python.org/3/library/tkinter.html)
[![Data Engine](https://img.shields.io/badge/Data%20Science-Pandas%20%7C%20NumPy-1565C0.svg)](https://pandas.pydata.org/)
[![Visualization](https://img.shields.io/badge/Visualization-Matplotlib-16A34A.svg)](https://matplotlib.org/)
[![Tests](https://img.shields.io/badge/Tests-23%20Passing%20%2F%20pytest-success.svg)](https://docs.pytest.org/)
[![Packaging](https://img.shields.io/badge/Packaging-PyInstaller-F59E0B.svg)](https://pyinstaller.org/)

---

## 1. Executive Overview

The **Store Management System** is a production-grade, desktop-based store administration and Point-of-Sale (POS) platform. Developed with an enterprise-grade modular architecture, it combines a modern desktop GUI with data science and analytical engines to manage inventory, products, suppliers, sales transactions, and shelf-life expiry dates.

### Core Capabilities:
- **Product Management:** Complete CRUD, instant multi-attribute search, category filtering, column sorting, and input schema validation.
- **Supplier Management:** Comprehensive supplier profiling with strict referential integrity guards preventing accidental orphan relationships.
- **Sales & POS Checkout:** Interactive cashier workflow with real-time price retrieval, stock sufficiency checks, atomic transactions, and digital receipt generation.
- **Inventory Tracking:** Stock-in (receiving deliveries), stock-out (damage write-offs / returns), physical audit reconciliation, and full chronological movement ledgers.
- **Expiry Notification System:** Automated shelf-life classification into four risk tiers (`EXPIRED`, `EXPIRING_SOON_7`, `EXPIRING_SOON_30`, `SAFE`), in-app acknowledgment, and direct batch disposal.
- **Data Science & Business Intelligence:** Live KPI scorecards, 30-day time-series revenue curves, category distribution bars, product demand rankings, and inventory health ratios rendered with Matplotlib.
- **Reliability & Data Protection:** Atomic CSV writes (`.tmp` write and atomic replace), thread-safe operations, and full ZIP backup creation/restoration with pre-restoration snapshots.

---

## 2. Architecture & File Structure

```
store_management_system/
│
├── main.py                     # Master GUI desktop launcher and shell
├── config.py                   # Global constants, paths, themes, typography
├── build_executable.py         # Automated PyInstaller packaging script
├── requirements.txt            # Python dependencies
├── README.md                   # Comprehensive documentation and manual
│
├── data/                       # CSV datasets (auto-generated if missing)
│   ├── products.csv            # 35+ products with prices, stock, expiry dates
│   ├── suppliers.csv           # 12+ verified commercial suppliers
│   ├── sales.csv               # 120+ historical sales transactions
│   ├── stock_movements.csv     # Complete reconciled movement ledger
│   └── expiry_alerts.csv       # Shelf-life risk tracking records
│
├── database/                   # Storage abstraction and backup layers
│   ├── __init__.py
│   ├── storage_manager.py      # Thread-safe DAO abstraction and atomic transactions
│   ├── csv_handler.py          # Atomic CSV reading/writing and synthetic data generator
│   └── backup_manager.py       # ZIP backup creation, listing, verification, and restore
│
├── modules/                    # Feature modules and GUI views
│   ├── __init__.py
│   ├── dashboard.py            # KPI summary cards and 4 embedded Matplotlib charts
│   ├── products.py             # Product CRUD, category filters, and sorting
│   ├── suppliers.py            # Supplier records and linked products viewer
│   ├── sales.py                # POS checkout and historical transactions
│   ├── inventory.py            # Stock-in, stock-out, reconciliation, and movement audit
│   ├── expiry_alerts.py        # Automated shelf-life tracking and disposal actions
│   ├── analytics.py            # Pure Pandas/NumPy business intelligence & visualizations
│   └── settings.py             # System diagnostics, log viewer, and backup manager
│
├── utils/                      # Helper utilities and validators
│   ├── __init__.py
│   ├── validators.py           # Strict schema, regex, numeric, and referential checks
│   ├── logger.py               # Rotating file and console logger
│   └── helpers.py              # Currency formatters, ID generators, and date logic
│
├── tests/                      # Automated pytest suite (isolated temporary data)
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures for directory isolation
│   ├── test_products.py        # Product CRUD and duplicate validation tests
│   ├── test_sales.py           # Sales calculations and atomic rollback tests
│   ├── test_inventory.py       # Stock movements and negative balance checks
│   ├── test_suppliers.py       # Referential integrity and deletion guards
│   └── test_expiry.py          # Shelf-life classification and alert tests
│
├── logs/                       # Rotating application activity and audit logs
├── backups/                    # Compressed ZIP backup archives
└── assets/                     # High-resolution charts and visual assets
```

---

## 3. Technology Stack

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Language** | Python | 3.9+ / 3.11+ | Core runtime language |
| **GUI Framework** | Tkinter & `ttk` | Built-in | Native desktop cross-platform UI |
| **Data Processing** | Pandas & NumPy | `>=2.0.0` / `>=1.24.0` | In-memory analytics, vector operations, grouping |
| **Data Visualization** | Matplotlib | `>=3.7.0` | Embedded figures via `FigureCanvasTkAgg` |
| **Data Storage** | CSV / Abstraction | Custom DAO | Atomic filesystem storage; ready for SQLite |
| **Testing** | Pytest | `>=7.0.0` | Automated unit, integration, and integrity tests |
| **Packaging** | PyInstaller | `>=6.0.0` | Standalone binary creation (.exe, .app, Linux binary) |

---

## 4. Five Custom Datasets & Reconciled Balances

The system automatically generates five realistic, internally consistent synthetic datasets if they do not exist:

1. **`products.csv`** (35 Products across 8 categories):
   - `product_id, product_name, category, supplier_id, purchase_price, selling_price, stock_quantity, minimum_stock, expiry_date`
2. **`suppliers.csv`** (12 Commercial Wholesale Partners):
   - `supplier_id, supplier_name, contact_number, email, address, product_category`
3. **`sales.csv`** (120+ Historical POS checkouts):
   - `transaction_id, product_id, sale_date, quantity, unit_price, total_amount`
4. **`stock_movements.csv`** (Reconciled movements):
   - `movement_id, product_id, movement_date, movement_type, quantity_change, notes`
   - Types: `INITIAL_STOCK`, `PURCHASE_RECEIPT`, `SALE`, `DAMAGED_WRITE_OFF`, `MANUAL_ADJUSTMENT`, `EXPIRED_DISPOSAL`
5. **`expiry_alerts.csv`** (Batch-level shelf-life tracking):
   - `alert_id, product_id, batch_number, expiry_date, quantity_affected, days_until_expiry, alert_status, notification_sent`

> **Mathematical Reconciliation Guarantee:** For every product, `stock_quantity = initial_stock + sum(purchases) - sum(sales) - sum(disposals) + sum(audit_adjustments)`.

---

## 5. Installation & Execution Guide

### Prerequisites
- Python 3.9, 3.10, or 3.11+ installed.
- Git (optional, for cloning).

---

### macOS Execution Instructions

1. **Open Terminal and navigate to the project directory:**
   ```bash
   cd /path/to/pds
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Launch the application:**
   ```bash
   python main.py
   ```
   *Or navigate into the module folder:*
   ```bash
   cd store_management_system
   python main.py
   ```

---

### Windows Execution Instructions

1. **Open PowerShell or Command Prompt:**
   ```powershell
   cd C:\path\to\pds
   ```
2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Launch the application:**
   ```powershell
   python main.py
   ```

---

### Linux (Ubuntu / Debian / Fedora) Execution Instructions

1. **Install Tkinter and Python development headers (if not present):**
   ```bash
   # Debian / Ubuntu / Mint
   sudo apt update && sudo apt install -y python3-tk python3-venv python3-pip

   # Fedora / RHEL
   sudo dnf install -y python3-tkinter python3-devel
   ```
2. **Setup virtual environment:**
   ```bash
   cd /path/to/pds
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Run the application:**
   ```bash
   python main.py
   ```

---

## 6. Running the Automated Test Suite

The project includes 23 automated tests covering product CRUD, duplicate rejections, referential integrity guards, atomic sale transactions, stock deduction, insufficient stock rejections, manual adjustments, and expiry classification.

Tests utilize pytest fixtures with `tmp_path` directory isolation so tests **never modify the real store data**.

To execute tests:
```bash
pytest -v store_management_system/tests
```

**Expected Output:**
```
============================== 23 passed in 0.38s ==============================
```

---

## 7. PyInstaller Packaging Instructions

The application is structured to support PyInstaller standalone executables across Windows, macOS, and Linux.

### Automated Build Script (Recommended)
Run the bundled build script:
```bash
python store_management_system/build_executable.py
```

### Manual Command
Alternatively, run PyInstaller directly:

**On macOS / Linux:**
```bash
pyinstaller --name "StoreManagementSystem" \
            --onedir \
            --windowed \
            --clean \
            --noconfirm \
            --add-data "store_management_system/data:data" \
            --add-data "store_management_system/assets:assets" \
            --hidden-import=pandas \
            --hidden-import=numpy \
            --hidden-import=matplotlib \
            --hidden-import=matplotlib.backends.backend_tkagg \
            store_management_system/main.py
```

**On Windows (PowerShell):**
```powershell
pyinstaller --name "StoreManagementSystem" `
            --onedir `
            --windowed `
            --clean `
            --noconfirm `
            --add-data "store_management_system/data;data" `
            --add-data "store_management_system/assets;assets" `
            --hidden-import=pandas `
            --hidden-import=numpy `
            --hidden-import=matplotlib `
            --hidden-import=matplotlib.backends.backend_tkagg `
            store_management_system\main.py
```

The resulting standalone executable package is placed in `dist/StoreManagementSystem/`.

---

## 8. College Project Presentation & Demonstration Walkthrough

When presenting this project, follow this structured walkthrough to demonstrate the full architectural and data science depth:

1. **Dashboard Overview:**
   - Showcase the 6 real-time KPI cards (Gross Revenue, Stock Units, Low-Stock items, Expired items).
   - Point out the 4 embedded Matplotlib charts (Sales Trend, Category Inventory, Top-Selling, and Stock Health).
   - Highlight the dynamic Warning Banner that alerts operators to items needing immediate restock or disposal.

2. **Point of Sale (POS) Workflow:**
   - Navigate to **Sales & POS Checkout**.
   - Select an item from the left product catalog (notice automatic price and current stock retrieval).
   - Attempt to enter a quantity greater than available stock — demonstrate that the system intercepts and blocks the sale with an "Insufficient Stock" alert.
   - Enter a valid quantity (e.g., 2), complete the sale, and display the official **Sales Receipt Modal**.
   - Show that product inventory decremented, a new transaction ID was minted, and an audit movement was recorded.

3. **Product Management & Referential Integrity:**
   - Navigate to **Product Management**.
   - Demonstrate multi-attribute search and category filtering.
   - Show that adding a product with a duplicate ID or negative price is rejected.
   - Navigate to **Supplier Management** and demonstrate the referential integrity guard: attempt to delete a supplier linked to active products. Show that the deletion is safely blocked with a list of linked product IDs.

4. **Inventory Control & Physical Stocktake Audit:**
   - Navigate to **Inventory & Movements**.
   - Show the inventory valuation scorecard ($ Cost, $ Retail, Margin %).
   - Open **Physical Audit Adjustment** and update an item's count (e.g., after a shelf audit).
   - Switch to the **Stock Movements Audit Ledger** tab to demonstrate that the adjustment was recorded as `MANUAL_ADJUSTMENT` with audit notes.

5. **Expiry Monitoring & Disposal:**
   - Navigate to **Expiry Notifications**.
   - Show the color-coded tiering (`EXPIRED`, `CRITICAL (1-7d)`, `WARNING (8-30d)`, `SAFE`).
   - Select an expired item and click **Initiate Stock Disposal (Write-Off)**.
   - Demonstrate that the stock quantity is cleared to 0 and logged as `EXPIRED_DISPOSAL`.

6. **Data Science & Analytics View:**
   - Navigate to **Data Science & Analytics**.
   - Switch between time filters (Last 7 Days, Last 30 Days, All Time) and watch the time-series charts update dynamically using Pandas aggregations.
   - Show the Best-Selling vs. Slow-Moving / Dead Stock risk tables.
   - Click **Export Analytics CSV** to demonstrate data reporting.

7. **Database Backups & Recovery:**
   - Navigate to **Backups & Settings**.
   - Click **Create Timestamped Backup Now** to create an on-demand ZIP archive of all 5 datasets.
   - Run **System Diagnostics** to display full row counts and referential integrity health.

---

## 9. Troubleshooting & FAQ

- **Q: Why does macOS show a Tk deprecation warning?**
  - **A:** Apple includes an older system Tk version in macOS. The application automatically silences this non-fatal warning using `TK_SILENCE_DEPRECATION=1`.
- **Q: What happens if a CSV file is accidentally deleted?**
  - **A:** The system automatically detects missing CSV files and safely initializes them or regenerates the synthetic datasets on launch.
- **Q: Can I restore data if a mistake is made?**
  - **A:** Yes! The system creates safety snapshots before destructive operations. You can also restore any prior snapshot from the **Backups & Settings** tab with one click.
- **Q: How can I migrate to SQLite in the future?**
  - **A:** All business logic calls the `StorageManager` Data Access Object (DAO) interface. Replacing the internal file I/O methods in `storage_manager.py` with SQL queries requires zero modifications to the GUI or analytics modules.

---

## 10. License & Author Information

Developed by the **Senior Python Software Architecture & Data Science Team**.
Released under the MIT License. Ready for academic evaluation, demonstration, and enterprise deployment.

