
"""
Sales Management Module for Store Management System.
Implements the Point-of-Sale (POS) checkout workflow, atomic transactions,
stock validation and deduction, stock movement recording, receipt generation,
and historical transaction reporting.
"""

from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd

from config import FONTS, THEME
from database.storage_manager import StorageManager
from utils.helpers import (
    export_dataframe_to_csv,
    format_currency,
    format_quantity,
    safe_float,
    safe_int,
)
from utils.logger import get_logger
from utils.validators import validate_sale_request

logger = get_logger("SalesModule")


class SalesManagementView(ttk.Frame):
    """
    Sales Management View with Tabs for New POS Checkout and Transaction History.
    """

    def __init__(
        self,
        parent: tk.Widget,
        storage: StorageManager,
        on_sale_completed=None,
        nav_callback=None
    ):
        super().__init__(parent)

        self.storage = storage
        self.on_sale_completed = on_sale_completed
        self.nav_callback = nav_callback

        self.selected_product = None
        self.unit_price_val = 0.0
        self.available_stock_val = 0

        self.df_products = pd.DataFrame()
        self.df_sales = pd.DataFrame()

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Top Header
        top_frame = tk.Frame(self, bg=THEME["gray_bg"])
        top_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(15, 8)
        )

        lbl_title = tk.Label(
            top_frame,
            text="Sales & POS Management",
            font=FONTS["h1"],
            bg=THEME["gray_bg"],
            fg=THEME["text_primary"],
        )
        lbl_title.pack(side="left")

        # Back to hub button
        if self.nav_callback:
            tk.Button(
                top_frame,
                text="← Back to CRUD Operations",
                command=lambda: self.nav_callback("hub"),
                bg=THEME.get("turquoise", "#028090"),
                fg=THEME["white"],
                font=FONTS["caption_bold"],
                relief="flat",
                padx=10,
                pady=3,
                cursor="hand2",
            ).pack(side="left", padx=(12, 0))

        # 2. Main Notebook
        notebook = ttk.Notebook(self)
        notebook.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(0, 15)
        )

        self.tab_pos = ttk.Frame(notebook)
        notebook.add(self.tab_pos, text=" 🛒 New POS Transaction ")

        self.tab_history = ttk.Frame(notebook)
        notebook.add(
            self.tab_history,
            text=" 📜 Sales Transaction History "
        )

        self._build_pos_tab()
        self._build_history_tab()

    # =========================================================================
    # POS CHECKOUT TAB
    # =========================================================================

    def _build_pos_tab(self):
        self.tab_pos.columnconfigure(0, weight=3)
        self.tab_pos.columnconfigure(1, weight=2)
        self.tab_pos.rowconfigure(0, weight=1)

        # Left Column: Product Selection Catalog
        catalog_frame = tk.LabelFrame(
            self.tab_pos,
            text=" 1. Select Product for Checkout ",
            font=FONTS["h3"],
            bg=THEME["white"],
            fg=THEME["text_primary"],
            padx=10,
            pady=10
        )
        catalog_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(10, 5),
            pady=10
        )
        catalog_frame.columnconfigure(0, weight=1)
        catalog_frame.rowconfigure(1, weight=1)

        # Search Bar
        cat_search_frame = tk.Frame(
            catalog_frame,
            bg=THEME["white"]
        )
        cat_search_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 8)
        )

        tk.Label(
            cat_search_frame,
            text="🔍 Search Products:",
            font=FONTS["body_bold"],
            bg=THEME["white"]
        ).pack(side="left", padx=(0, 5))

        self.pos_search_entry = ttk.Entry(
            cat_search_frame,
            width=28
        )
        self.pos_search_entry.pack(
            side="left",
            padx=(0, 10)
        )
        self.pos_search_entry.bind(
            "<KeyRelease>",
            lambda e: self._filter_pos_catalog()
        )

        # Catalog Tree
        cols = (
            "id", "name", "category",
            "price", "stock", "status"
        )

        self.tree_pos_catalog = ttk.Treeview(
            catalog_frame,
            columns=cols,
            show="headings",
            selectmode="browse"
        )

        self.tree_pos_catalog.heading("id", text="ID")
        self.tree_pos_catalog.heading("name", text="Product Name")
        self.tree_pos_catalog.heading("category", text="Category")
        self.tree_pos_catalog.heading("price", text="Price (₹)")
        self.tree_pos_catalog.heading("stock", text="In Stock")
        self.tree_pos_catalog.heading("status", text="Stock Status")

        self.tree_pos_catalog.column(
            "id", width=70, anchor="center"
        )
        self.tree_pos_catalog.column(
            "name", width=180, anchor="w"
        )
        self.tree_pos_catalog.column(
            "category", width=100, anchor="w"
        )
        self.tree_pos_catalog.column(
            "price", width=70, anchor="e"
        )
        self.tree_pos_catalog.column(
            "stock", width=60, anchor="center"
        )
        self.tree_pos_catalog.column(
            "status", width=85, anchor="center"
        )

        sb = ttk.Scrollbar(
            catalog_frame,
            orient="vertical",
            command=self.tree_pos_catalog.yview
        )
        self.tree_pos_catalog.configure(
            yscrollcommand=sb.set
        )

        self.tree_pos_catalog.grid(
            row=1,
            column=0,
            sticky="nsew"
        )
        sb.grid(row=1, column=1, sticky="ns")

        self.tree_pos_catalog.bind(
            "<<TreeviewSelect>>",
            self._on_catalog_product_selected
        )

        # Right Column: Order Checkout Card
        order_frame = tk.LabelFrame(
            self.tab_pos,
            text=" 2. Transaction Details & Payment ",
            font=FONTS["h3"],
            bg=THEME["white"],
            fg=THEME["text_primary"],
            padx=15,
            pady=15
        )
        order_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(5, 10),
            pady=10
        )
        order_frame.columnconfigure(1, weight=1)

        row = 0

        tk.Label(
            order_frame,
            text="Selected Item:",
            font=FONTS["body_bold"],
            bg=THEME["white"],
            anchor="w"
        ).grid(row=row, column=0, sticky="w", pady=6)

        self.lbl_selected_name = tk.Label(
            order_frame,
            text="-- Please select from catalog --",
            font=FONTS["body_bold"],
            bg=THEME["white"],
            fg=THEME["navy_accent"],
            anchor="w"
        )
        self.lbl_selected_name.grid(
            row=row,
            column=1,
            sticky="w",
            pady=6
        )

        row += 1

        tk.Label(
            order_frame,
            text="Product ID:",
            font=FONTS["body"],
            bg=THEME["white"],
            anchor="w"
        ).grid(row=row, column=0, sticky="w", pady=4)

        self.lbl_selected_id = tk.Label(
            order_frame,
            text="--",
            font=FONTS["body"],
            bg=THEME["white"],
            fg=THEME["text_secondary"],
            anchor="w"
        )
        self.lbl_selected_id.grid(
            row=row,
            column=1,
            sticky="w",
            pady=4
        )

        row += 1

        tk.Label(
            order_frame,
            text="Unit Price:",
            font=FONTS["body"],
            bg=THEME["white"],
            anchor="w"
        ).grid(row=row, column=0, sticky="w", pady=4)

        self.lbl_unit_price = tk.Label(
            order_frame,
            text="₹0.00",
            font=FONTS["body_bold"],
            bg=THEME["white"],
            fg=THEME["text_primary"],
            anchor="w"
        )
        self.lbl_unit_price.grid(
            row=row,
            column=1,
            sticky="w",
            pady=4
        )

        row += 1

        tk.Label(
            order_frame,
            text="Available Stock:",
            font=FONTS["body"],
            bg=THEME["white"],
            anchor="w"
        ).grid(row=row, column=0, sticky="w", pady=4)

        self.lbl_avail_stock = tk.Label(
            order_frame,
            text="0 units",
            font=FONTS["body_bold"],
            bg=THEME["white"],
            fg=THEME["text_secondary"],
            anchor="w"
        )
        self.lbl_avail_stock.grid(
            row=row,
            column=1,
            sticky="w",
            pady=4
        )

        row += 1

        ttk.Separator(
            order_frame,
            orient="horizontal"
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10
        )

        # Quantity Input
        row += 1

        tk.Label(
            order_frame,
            text="Sale Quantity:",
            font=FONTS["body_bold"],
            bg=THEME["white"],
            anchor="w"
        ).grid(row=row, column=0, sticky="w", pady=6)

        qty_box = tk.Frame(
            order_frame,
            bg=THEME["white"]
        )
        qty_box.grid(
            row=row,
            column=1,
            sticky="w",
            pady=6
        )

        self.spin_qty = tk.Spinbox(
            qty_box,
            from_=1,
            to=1000,
            width=8,
            font=FONTS["body_bold"],
            command=self._calculate_total
        )
        self.spin_qty.pack(side="left")
        self.spin_qty.delete(0, tk.END)
        self.spin_qty.insert(0, "1")
        self.spin_qty.bind(
            "<KeyRelease>",
            lambda e: self._calculate_total()
        )

        row += 1

        tk.Label(
            order_frame,
            text="Sale Date:",
            font=FONTS["body"],
            bg=THEME["white"],
            anchor="w"
        ).grid(row=row, column=0, sticky="w", pady=6)

        self.entry_sale_date = ttk.Entry(
            order_frame,
            width=15
        )
        self.entry_sale_date.insert(
            0,
            date.today().strftime("%Y-%m-%d")
        )
        self.entry_sale_date.grid(
            row=row,
            column=1,
            sticky="w",
            pady=6
        )

        row += 1

        ttk.Separator(
            order_frame,
            orient="horizontal"
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10
        )

        # Total Amount
        row += 1

        tk.Label(
            order_frame,
            text="TOTAL AMOUNT:",
            font=FONTS["h2"],
            bg=THEME["white"],
            fg=THEME["navy_dark"],
            anchor="w"
        ).grid(row=row, column=0, sticky="w", pady=10)

        self.lbl_total_amount = tk.Label(
            order_frame,
            text="₹0.00",
            font=FONTS["card_value"],
            bg=THEME["white"],
            fg=THEME["success"],
            anchor="w"
        )
        self.lbl_total_amount.grid(
            row=row,
            column=1,
            sticky="w",
            pady=10
        )

        # Checkout Button
        row += 1

        self.btn_checkout = tk.Button(
            order_frame,
            text="✓ Complete Sale & Deduct Stock",
            command=self._execute_sale,
            bg=THEME["success"],
            fg=THEME["white"],
            font=FONTS["h3"],
            relief="flat",
            padx=16,
            pady=10,
            cursor="hand2",
            state="disabled",
        )
        self.btn_checkout.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(15, 0)
        )

    def _filter_pos_catalog(self):
        """Filters catalog table based on user search."""

        for item in self.tree_pos_catalog.get_children():
            self.tree_pos_catalog.delete(item)

        if self.df_products.empty:
            return

        df = self.df_products.copy()
        query = self.pos_search_entry.get().strip().lower()

        if query:
            product_id = df["product_id"].fillna("").astype(str)
            product_name = df["product_name"].fillna("").astype(str)
            category = df["category"].fillna("").astype(str)

            df = df[
                product_id.str.lower().str.contains(query, na=False)
                | product_name.str.lower().str.contains(query, na=False)
                | category.str.lower().str.contains(query, na=False)
            ]

        for _, row in df.iterrows():
            stock = safe_int(row["stock_quantity"])

            status = (
                "In Stock"
                if stock > 5
                else ("Low Stock" if stock > 0 else "Out of Stock")
            )

            self.tree_pos_catalog.insert(
                "",
                "end",
                values=(
                    row["product_id"],
                    row["product_name"],
                    row["category"],
                    f"₹{safe_float(row['selling_price']):.2f}",
                    stock,
                    status,
                ),
            )

    def _on_catalog_product_selected(self, event=None):
        """Triggered when a product is selected."""

        selected = self.tree_pos_catalog.selection()

        if not selected:
            return

        values = self.tree_pos_catalog.item(
            selected[0],
            "values"
        )

        pid = values[0]
        pname = values[1]
        price_str = values[3].replace("$", "").replace("₹", "").strip()
        stock_str = values[4]

        self.selected_product = pid
        self.unit_price_val = safe_float(price_str)
        self.available_stock_val = safe_int(stock_str)

        self.lbl_selected_name.config(text=pname)
        self.lbl_selected_id.config(text=pid)

        self.lbl_unit_price.config(
            text=format_currency(self.unit_price_val)
        )

        self.lbl_avail_stock.config(
            text=f"{self.available_stock_val} units",
            fg=(
                THEME["danger"]
                if self.available_stock_val <= 0
                else THEME["text_secondary"]
            )
        )

        if self.available_stock_val > 0:
            self.btn_checkout.config(
                state="normal",
                bg=THEME["success"]
            )
        else:
            self.btn_checkout.config(
                state="disabled",
                bg=THEME["gray_border"]
            )

        self._calculate_total()

    def _calculate_total(self):
        """Calculates total cost in real time."""

        try:
            qty = int(self.spin_qty.get())

            if qty <= 0:
                self.lbl_total_amount.config(
                    text="₹0.00",
                    fg=THEME["danger"]
                )
                return

            total = qty * self.unit_price_val

            self.lbl_total_amount.config(
                text=format_currency(total),
                fg=THEME["success"]
            )

        except ValueError:
            self.lbl_total_amount.config(text="₹0.00")

    def _execute_sale(self):
        """Validates and completes the sale."""

        if not self.selected_product:
            messagebox.showinfo(
                "Product Required",
                "Please select a product from the catalog."
            )
            return

        qty_raw = self.spin_qty.get()

        is_valid, msg, qty, total_amount = validate_sale_request(
            self.selected_product,
            qty_raw,
            self.available_stock_val,
            self.unit_price_val
        )

        if not is_valid:
            messagebox.showerror("Sale Rejected", msg)
            return

        sale_dt = self.entry_sale_date.get().strip()

        # Validate sale date.
        try:
            datetime.strptime(sale_dt, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Invalid Sale Date",
                "Please enter the sale date in YYYY-MM-DD format."
            )
            return

        # Execute sale through storage transaction.
        try:
            success, exec_msg, receipt = self.storage.record_sale(
                product_id=self.selected_product,
                quantity=qty,
                unit_price=self.unit_price_val,
                sale_date=sale_dt
            )

        except Exception as exc:
            logger.exception("Sale transaction failed.")
            messagebox.showerror(
                "Transaction Failed",
                str(exc)
            )
            return

        if success and receipt:
            self._show_receipt_modal(receipt)
            self.load_data()

            if self.on_sale_completed:
                self.on_sale_completed()

        else:
            messagebox.showerror(
                "Transaction Failed",
                exec_msg
            )

    def _show_receipt_modal(self, receipt: dict):
        """Displays a POS receipt modal."""

        modal = tk.Toplevel(self)
        modal.title(f"Receipt - {receipt['transaction_id']}")
        modal.geometry("420x460")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        receipt_box = tk.Frame(
            modal,
            bg=THEME["white"],
            bd=2,
            relief="solid",
            padx=20,
            pady=20
        )
        receipt_box.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        tk.Label(
            receipt_box,
            text="STORE MANAGEMENT SYSTEM",
            font=FONTS["h2"],
            bg=THEME["white"],
            fg=THEME["navy_primary"]
        ).pack()

        tk.Label(
            receipt_box,
            text="OFFICIAL SALES RECEIPT",
            font=FONTS["caption_bold"],
            bg=THEME["white"],
            fg=THEME["text_muted"]
        ).pack(pady=(0, 10))

        ttk.Separator(
            receipt_box,
            orient="horizontal"
        ).pack(fill="x", pady=6)

        info = [
            ("Transaction ID:", receipt["transaction_id"]),
            ("Date:", receipt["sale_date"]),
            ("Product:", receipt["product_name"]),
            ("Product ID:", receipt["product_id"]),
            ("Quantity:", f"{receipt['quantity']} units"),
            ("Unit Price:", format_currency(receipt["unit_price"])),
            (
                "Remaining Stock:",
                f"{receipt['remaining_stock']} units"
            ),
        ]

        for lbl, val in info:
            frame = tk.Frame(
                receipt_box,
                bg=THEME["white"]
            )
            frame.pack(fill="x", pady=2)

            tk.Label(
                frame,
                text=lbl,
                font=FONTS["body"],
                bg=THEME["white"],
                fg=THEME["text_secondary"]
            ).pack(side="left")

            tk.Label(
                frame,
                text=val,
                font=FONTS["body_bold"],
                bg=THEME["white"],
                fg=THEME["text_primary"]
            ).pack(side="right")

        ttk.Separator(
            receipt_box,
            orient="horizontal"
        ).pack(fill="x", pady=10)

        tot_frame = tk.Frame(
            receipt_box,
            bg=THEME["white"]
        )
        tot_frame.pack(fill="x", pady=5)

        tk.Label(
            tot_frame,
            text="TOTAL PAID:",
            font=FONTS["h2"],
            bg=THEME["white"],
            fg=THEME["navy_dark"]
        ).pack(side="left")

        tk.Label(
            tot_frame,
            text=format_currency(receipt["total_amount"]),
            font=FONTS["card_value"],
            bg=THEME["white"],
            fg=THEME["success"]
        ).pack(side="right")

        tk.Label(
            receipt_box,
            text="✓ Payment Successful & Stock Ledger Updated",
            font=FONTS["caption_bold"],
            bg=THEME["white"],
            fg=THEME["success"]
        ).pack(pady=(12, 10))

        tk.Button(
            receipt_box,
            text="Done / Close Receipt",
            command=modal.destroy,
            font=FONTS["caption_bold"],
            bg=THEME["navy_accent"],
            fg=THEME["white"],
            relief="flat",
            padx=15,
            pady=6
        ).pack()

    # =========================================================================
    # TRANSACTION HISTORY TAB
    # =========================================================================

    def _build_history_tab(self):
        self.tab_history.columnconfigure(0, weight=1)
        self.tab_history.rowconfigure(2, weight=1)

        # Summary KPIs
        self.history_kpi_frame = tk.Frame(
            self.tab_history,
            bg=THEME["gray_bg"]
        )
        self.history_kpi_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=10,
            pady=(10, 8)
        )

        for i in range(4):
            self.history_kpi_frame.columnconfigure(i, weight=1)

        # Filters Bar
        filter_frame = tk.Frame(
            self.tab_history,
            bg=THEME["white"],
            bd=1,
            relief="solid",
            padx=10,
            pady=8
        )
        filter_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=10,
            pady=(0, 8)
        )

        tk.Label(
            filter_frame,
            text="🔍 Search:",
            font=FONTS["body_bold"],
            bg=THEME["white"]
        ).pack(side="left", padx=(0, 5))

        self.entry_hist_search = ttk.Entry(
            filter_frame,
            width=22
        )
        self.entry_hist_search.pack(
            side="left",
            padx=(0, 15)
        )
        self.entry_hist_search.bind(
            "<KeyRelease>",
            lambda e: self.filter_history()
        )

        tk.Label(
            filter_frame,
            text="Date Range:",
            font=FONTS["body_bold"],
            bg=THEME["white"]
        ).pack(side="left", padx=(0, 5))

        self.combo_hist_range = ttk.Combobox(
            filter_frame,
            state="readonly",
            values=[
                "All Time",
                "Today",
                "Last 7 Days",
                "Last 30 Days"
            ],
            width=14
        )
        self.combo_hist_range.set("All Time")
        self.combo_hist_range.pack(
            side="left",
            padx=(0, 15)
        )
        self.combo_hist_range.bind(
            "<<ComboboxSelected>>",
            lambda e: self.filter_history()
        )

        btn_export = tk.Button(
            filter_frame,
            text="📥 Export Sales CSV",
            command=self._export_sales_csv,
            bg=THEME["white"],
            fg=THEME["navy_accent"],
            bd=1,
            relief="solid",
            font=FONTS["caption_bold"],
            padx=10,
            pady=3,
            cursor="hand2"
        )
        btn_export.pack(side="right")

        self.lbl_hist_count = tk.Label(
            filter_frame,
            text="",
            font=FONTS["caption_bold"],
            bg=THEME["white"],
            fg=THEME["text_muted"]
        )
        self.lbl_hist_count.pack(
            side="right",
            padx=15
        )

        # History Tree Table
        tree_frame = tk.Frame(
            self.tab_history,
            bg=THEME["white"],
            bd=1,
            relief="solid"
        )
        tree_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=10,
            pady=(0, 10)
        )
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        cols = (
            "tx_id", "product_id", "product_name",
            "date", "qty", "unit_price", "total"
        )

        self.tree_history = ttk.Treeview(
            tree_frame,
            columns=cols,
            show="headings"
        )

        self.tree_history.heading(
            "tx_id",
            text="Transaction ID"
        )
        self.tree_history.heading(
            "product_id",
            text="Product ID"
        )
        self.tree_history.heading(
            "product_name",
            text="Product Name"
        )
        self.tree_history.heading(
            "date",
            text="Sale Date"
        )
        self.tree_history.heading(
            "qty",
            text="Quantity"
        )
        self.tree_history.heading(
            "unit_price",
            text="Unit Price (₹)"
        )
        self.tree_history.heading(
            "total",
            text="Total Amount (₹)"
        )

        self.tree_history.column(
            "tx_id", width=100, anchor="center"
        )
        self.tree_history.column(
            "product_id", width=90, anchor="center"
        )
        self.tree_history.column(
            "product_name", width=220, anchor="w"
        )
        self.tree_history.column(
            "date", width=100, anchor="center"
        )
        self.tree_history.column(
            "qty", width=70, anchor="center"
        )
        self.tree_history.column(
            "unit_price", width=90, anchor="e"
        )
        self.tree_history.column(
            "total", width=100, anchor="e"
        )

        sb = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree_history.yview
        )
        self.tree_history.configure(
            yscrollcommand=sb.set
        )

        self.tree_history.grid(
            row=0,
            column=0,
            sticky="nsew"
        )
        sb.grid(row=0, column=1, sticky="ns")

    def load_data(self):
        """Refresh product list and sales history."""

        self.df_products = self.storage.get_products()
        self.df_sales = self.storage.get_sales()

        self._filter_pos_catalog()
        self.filter_history()

    def filter_history(self):
        """Apply date and text filters and update summary KPIs."""

        for item in self.tree_history.get_children():
            self.tree_history.delete(item)

        if self.df_sales.empty:
            self._render_history_kpis(0.0, 0, 0)
            self.lbl_hist_count.config(text="0 transactions")
            return

        df = self.df_sales.copy()

        # Ensure numeric columns.
        df["total_amount_num"] = pd.to_numeric(
            df["total_amount"],
            errors="coerce"
        ).fillna(0.0)

        df["quantity_num"] = pd.to_numeric(
            df["quantity"],
            errors="coerce"
        ).fillna(0)

        # Correct product-name mapping.
        if "product_name" in df.columns and not df.empty:

            if (
                not self.df_products.empty
                and "product_name" in self.df_products.columns
                and "product_id" in self.df_products.columns
            ):
                name_map = dict(
                    zip(
                        self.df_products["product_id"],
                        self.df_products["product_name"]
                    )
                )

                df["product_name"] = (
                    df["product_name"]
                    .replace("", None)
                    .fillna(df["product_id"].map(name_map))
                    .fillna("Unknown Product")
                )

            else:
                df["product_name"] = (
                    df["product_name"].fillna("Unknown Product")
                )

        elif (
            not self.df_products.empty
            and "product_id" in self.df_products.columns
            and "product_name" in self.df_products.columns
        ):
            df = df.merge(
                self.df_products[["product_id", "product_name"]],
                on="product_id",
                how="left"
            )

            if "product_name" not in df.columns:
                df["product_name"] = "Unknown Product"

            df["product_name"] = (
                df["product_name"].fillna("Unknown Product")
            )

        else:
            df["product_name"] = "Unknown Product"

        df["product_name"] = (
            df["product_name"].fillna("Unknown Product")
        )

        # 1. Search Query
        query = self.entry_hist_search.get().strip().lower()

        if query:
            transaction_id = (
                df["transaction_id"].fillna("").astype(str)
                if "transaction_id" in df.columns
                else pd.Series("", index=df.index)
            )

            product_id = (
                df["product_id"].fillna("").astype(str)
                if "product_id" in df.columns
                else pd.Series("", index=df.index)
            )

            product_name = (
                df["product_name"].fillna("").astype(str)
            )

            df = df[
                transaction_id.str.lower().str.contains(
                    query, na=False
                )
                | product_id.str.lower().str.contains(
                    query, na=False
                )
                | product_name.str.lower().str.contains(
                    query, na=False
                )
            ]

        # 2. Date Range Filter
        range_choice = self.combo_hist_range.get()
        today = date.today()

        if range_choice == "Today":
            today_str = today.strftime("%Y-%m-%d")
            df = df[df["sale_date"].astype(str) == today_str]

        elif range_choice == "Last 7 Days":
            cutoff = (
                today - timedelta(days=7)
            ).strftime("%Y-%m-%d")

            df = df[
                df["sale_date"].astype(str) >= cutoff
            ]

        elif range_choice == "Last 30 Days":
            cutoff = (
                today - timedelta(days=30)
            ).strftime("%Y-%m-%d")

            df = df[
                df["sale_date"].astype(str) >= cutoff
            ]

        # Sort newest transactions first.
        df = df.sort_values(
            by="sale_date",
            ascending=False
        )

        # Populate transaction rows.
        for _, row in df.iterrows():
            self.tree_history.insert(
                "",
                "end",
                values=(
                    row.get("transaction_id", ""),
                    row.get("product_id", ""),
                    row.get("product_name", "Unknown Product"),
                    row.get("sale_date", ""),
                    int(row["quantity_num"]),
                    f"₹{safe_float(row.get('unit_price', 0)):.2f}",
                    f"₹{row['total_amount_num']:.2f}",
                ),
            )

        # Calculate KPIs for the filtered result.
        total_revenue = df["total_amount_num"].sum()
        total_quantity = int(df["quantity_num"].sum())
        total_transactions = len(df)

        self._render_history_kpis(
            total_revenue,
            total_transactions,
            total_quantity
        )

        self.lbl_hist_count.config(
            text=(
                f"Showing {total_transactions} "
                f"of {len(self.df_sales)} sales"
            )
        )

    def _render_history_kpis(
        self,
        revenue: float,
        tx_count: int,
        units_sold: int
    ):
        """Render sales summary KPI cards."""

        for widget in self.history_kpi_frame.winfo_children():
            widget.destroy()

        avg_tx = (
            revenue / tx_count
            if tx_count > 0
            else 0.0
        )

        cards = [
            (
                "Selected Period Revenue",
                format_currency(revenue),
                THEME["success"]
            ),
            (
                "Total Transactions",
                format_quantity(tx_count),
                THEME["navy_accent"]
            ),
            (
                "Total Units Sold",
                format_quantity(units_sold),
                THEME["info"]
            ),
            (
                "Average Ticket Size",
                format_currency(avg_tx),
                THEME["text_secondary"]
            ),
        ]

        for i, (title, value, color) in enumerate(cards):
            card = tk.Frame(
                self.history_kpi_frame,
                bg=THEME["white"],
                bd=1,
                relief="solid",
                padx=8,
                pady=6
            )
            card.grid(
                row=0,
                column=i,
                padx=3,
                sticky="ew"
            )

            tk.Label(
                card,
                text=title,
                font=FONTS["card_title"],
                bg=THEME["white"],
                fg=THEME["text_muted"]
            ).pack(anchor="w")

            tk.Label(
                card,
                text=value,
                font=FONTS["card_value"],
                bg=THEME["white"],
                fg=color
            ).pack(
                anchor="w",
                pady=(1, 0)
            )

    def _export_sales_csv(self):
        """Exports sales transactions dataset to CSV."""

        if self.df_sales.empty:
            messagebox.showinfo(
                "Export",
                "No sales records available to export."
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialfile=(
                f"sales_transactions_"
                f"{date.today().strftime('%Y%m%d')}.csv"
            )
        )

        if not file_path:
            return

        ok, msg = export_dataframe_to_csv(
            self.df_sales,
            file_path
        )

        if ok:
            messagebox.showinfo(
                "Export Complete",
                msg
            )
        else:
            messagebox.showerror(
                "Export Failed",
                msg
            )
