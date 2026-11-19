"""
Dedicated CRUD Operation Views for Store Management System.
Faithfully reproduces the reference four independent operation pages:
1. Create (Operation 1): CATALOGIX Add New Product
   - Basic Information, Selling Information (toggle), Purchase Information (toggle),
     Product Image preview, Dimensions, Inventory Control, and Valuation Method.
2. Update (Operation 3): KANGAROO Edit / Update Product
   - Soft lavender/pink backdrop, Product selector, SKU, Barcode, Returnable toggle,
     Dimensions & Weights grid, Apply and Edit Product actions.
3. Delete (Operation 4): Safe Deletion with Confirmation Modal
   - Product table with checkboxes, floating Delete Product confirmation modal:
     Red warning badge, 'Delete product', confirmation message, Cancel and Delete buttons.
"""

from datetime import date
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
from PIL import Image, ImageTk

# Base directory setup
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from config import ASSETS_DIR, FONTS, THEME
except Exception:
    ASSETS_DIR = BASE_DIR / "assets"
    FONTS = {}
    THEME = {}

from database.storage_manager import StorageManager
from utils.helpers import calculate_days_until, format_currency, generate_next_id, safe_float, safe_int
from utils.logger import get_logger
from utils.validators import validate_product_data

logger = get_logger("CRUDOperations")


# =============================================================================
# 1. CREATE PRODUCT VIEW (CATALOGIX - OPERATION 1)
# =============================================================================

class CreateProductView(ttk.Frame):
    """
    Operation 1: CREATE – CATALOGIX Add New Product matching reference design.
    """

    def __init__(self, parent: tk.Widget, storage: StorageManager, nav_callback=None):
        super().__init__(parent)
        self.storage = storage
        self.nav_callback = nav_callback
        self.entries = {}

        self._build_ui()
        self.reset_form()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Outer Container (#F8FAFC)
        container = tk.Frame(self, bg="#F8FAFC")
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        # ── LEFT SIDEBAR: CATALOGIX ──────────────────────────────────────────
        sidebar = tk.Frame(container, bg="#FFFFFF", width=200, bd=1, relief="solid")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Logo
        tk.Label(
            sidebar,
            text="CATALOGIX",
            font=("Arial", 14, "bold"),
            fg="#2563EB",
            bg="#FFFFFF"
        ).pack(anchor="w", padx=18, pady=(18, 20))

        menu_items = [
            ("Dashboard", False),
            ("Product", True),
            ("Inventory", False),
            ("Sales", False),
            ("Purchase", False),
            ("Accounting", False),
            ("Reports", False),
            ("User & Roles", False),
            ("Settings", False),
        ]

        for title, is_active in menu_items:
            bg_col = "#EFF6FF" if is_active else "#FFFFFF"
            fg_col = "#2563EB" if is_active else "#64748B"
            f = tk.Frame(sidebar, bg=bg_col, padx=14, pady=6)
            f.pack(fill="x", padx=10, pady=2)
            lbl = tk.Label(f, text=title, font=("Arial", 10, "bold" if is_active else "normal"), fg=fg_col, bg=bg_col)
            lbl.pack(anchor="w")

            if is_active:
                # Sub-menu under Product
                sub_f = tk.Frame(sidebar, bg="#FFFFFF", padx=24)
                sub_f.pack(fill="x")
                for sub in ["• All Products", "• Add New Product", "• Categories", "• Brands"]:
                    sub_col = "#2563EB" if "Add New" in sub else "#94A3B8"
                    tk.Label(sub_f, text=sub, font=("Arial", 9), fg=sub_col, bg="#FFFFFF").pack(anchor="w", pady=2)

        # ── MAIN FORM AREA ───────────────────────────────────────────────────
        main_frame = tk.Frame(container, bg="#F8FAFC")
        main_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Top Header Bar (Breadcrumb + Actions)
        top_bar = tk.Frame(main_frame, bg="#FFFFFF", height=60, padx=24, pady=10, bd=1, relief="solid")
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_propagate(False)

        bread_box = tk.Frame(top_bar, bg="#FFFFFF")
        bread_box.pack(side="left")

        tk.Label(bread_box, text="Product / Product Management / Add New Product", font=("Arial", 9), fg="#94A3B8", bg="#FFFFFF").pack(anchor="w")
        tk.Label(bread_box, text="Add New Product", font=("Arial", 14, "bold"), fg="#1E293B", bg="#FFFFFF").pack(anchor="w")

        btn_box = tk.Frame(top_bar, bg="#FFFFFF")
        btn_box.pack(side="right")

        btn_cancel = tk.Button(
            btn_box,
            text="Cancel",
            font=("Arial", 10),
            fg="#64748B",
            bg="#FFFFFF",
            relief="solid",
            bd=1,
            padx=14,
            pady=4,
            cursor="hand2",
            command=lambda: self._navigate_to("hub")
        )
        btn_cancel.pack(side="left", padx=(0, 10))

        btn_save = tk.Button(
            btn_box,
            text="Save Product",
            font=("Arial", 10, "bold"),
            fg="#FFFFFF",
            bg="#2563EB",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=16,
            pady=4,
            cursor="hand2",
            command=self._submit_create
        )
        btn_save.pack(side="left")

        # Scrollable Form Content
        canvas = tk.Canvas(main_frame, bg="#F8FAFC", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        form_content = tk.Frame(canvas, bg="#F8FAFC", padx=24, pady=16)

        canvas.create_window((0, 0), window=form_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        form_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(1, width=e.width))

        # Two-Column Layout for Form Cards
        form_content.columnconfigure(0, weight=62, uniform="create_col")
        form_content.columnconfigure(1, weight=38, uniform="create_col")

        # ── LEFT FORM COLUMN: Basic, Selling & Purchase Info ─────────────────
        left_col = tk.Frame(form_content, bg="#F8FAFC")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        # 1. Basic Information Card
        card_basic = tk.Frame(left_col, bg="#FFFFFF", bd=1, relief="solid", padx=18, pady=14)
        card_basic.pack(fill="x", pady=(0, 14))

        tk.Label(card_basic, text="Basic Information", font=("Arial", 12, "bold"), fg="#1E293B", bg="#FFFFFF").pack(anchor="w", pady=(0, 10))

        grid_basic = tk.Frame(card_basic, bg="#FFFFFF")
        grid_basic.pack(fill="x")
        grid_basic.columnconfigure(0, weight=1)
        grid_basic.columnconfigure(1, weight=1)

        self._add_field(grid_basic, "Product Name*", "entry_name", "Organic Sweet Corn 500g", 0, 0)
        self._add_field(grid_basic, "SKU*", "entry_sku", "SKU-9921", 0, 1)
        self._add_field(grid_basic, "Product Code*", "entry_id", "PRD-0036", 1, 0)
        self._add_field(grid_basic, "Unit", "entry_unit", "Box / Pack", 1, 1)

        tk.Label(grid_basic, text="Category*", font=("Arial", 9, "bold"), fg="#475569", bg="#FFFFFF").grid(row=4, column=0, sticky="w", pady=(6, 2))
        combo_cat = ttk.Combobox(
            grid_basic,
            values=["Fresh Produce", "Beverages", "Dairy & Eggs", "Bakery", "Pantry", "Snacks", "Meat & Deli"],
            state="readonly"
        )
        combo_cat.set("Fresh Produce")
        combo_cat.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.entries["combo_category"] = combo_cat

        # 2. Selling Information Card (with green toggle)
        card_selling = tk.Frame(left_col, bg="#FFFFFF", bd=1, relief="solid", padx=18, pady=14)
        card_selling.pack(fill="x", pady=(0, 14))

        hdr_sell = tk.Frame(card_selling, bg="#FFFFFF")
        hdr_sell.pack(fill="x", pady=(0, 10))
        tk.Label(hdr_sell, text="Selling Information", font=("Arial", 12, "bold"), fg="#1E293B", bg="#FFFFFF").pack(side="left")
        tk.Label(hdr_sell, text="● Enabled", font=("Arial", 9, "bold"), fg="#10B981", bg="#ECFDF5", padx=8, pady=2).pack(side="right")

        grid_sell = tk.Frame(card_selling, bg="#FFFFFF")
        grid_sell.pack(fill="x")
        grid_sell.columnconfigure(0, weight=1)
        grid_sell.columnconfigure(1, weight=1)

        self._add_field(grid_sell, "Selling Price (₹)*", "entry_price", "3.49", 0, 0)
        self._add_field(grid_sell, "Manufacturer", "entry_mfg", "FreshFarms Agro", 0, 1)
        self._add_field(grid_sell, "Discount (%)", "entry_disc", "5", 1, 0)
        self._add_field(grid_sell, "Tax Sale (%)", "entry_tax", "8", 1, 1)
        self._add_field(grid_sell, "Sales Description", "entry_desc", "Fresh crisp organic sweet corn.", 2, 0, colspan=2)

        # 3. Purchase Information Card (with green toggle)
        card_purch = tk.Frame(left_col, bg="#FFFFFF", bd=1, relief="solid", padx=18, pady=14)
        card_purch.pack(fill="x")

        hdr_purch = tk.Frame(card_purch, bg="#FFFFFF")
        hdr_purch.pack(fill="x", pady=(0, 10))
        tk.Label(hdr_purch, text="Purchase Information", font=("Arial", 12, "bold"), fg="#1E293B", bg="#FFFFFF").pack(side="left")
        tk.Label(hdr_purch, text="● Enabled", font=("Arial", 9, "bold"), fg="#10B981", bg="#ECFDF5", padx=8, pady=2).pack(side="right")

        grid_purch = tk.Frame(card_purch, bg="#FFFFFF")
        grid_purch.pack(fill="x")
        grid_purch.columnconfigure(0, weight=1)
        grid_purch.columnconfigure(1, weight=1)

        self._add_field(grid_purch, "Purchase Cost (₹)*", "entry_cost", "1.80", 0, 0)
        self._add_field(grid_purch, "Preferred Vendor", "combo_supplier", "SUP-004", 0, 1)
        self._add_field(grid_purch, "Initial Stock Quantity*", "entry_stock", "45", 1, 0)
        self._add_field(grid_purch, "Minimum Reorder Level*", "entry_min", "12", 1, 1)
        self._add_field(grid_purch, "Expiry Date (YYYY-MM-DD)", "entry_expiry", (date.today() + pd.Timedelta(days=120)).strftime("%Y-%m-%d"), 2, 0, colspan=2)

        # ── RIGHT FORM COLUMN: Product Image, Dimensions, Inventory Control ─
        right_col = tk.Frame(form_content, bg="#F8FAFC")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        # 1. Product Image Card
        card_img = tk.Frame(right_col, bg="#FFFFFF", bd=1, relief="solid", padx=16, pady=14)
        card_img.pack(fill="x", pady=(0, 14))

        tk.Label(card_img, text="Product Image", font=("Arial", 12, "bold"), fg="#1E293B", bg="#FFFFFF").pack(anchor="w", pady=(0, 10))

        img_row = tk.Frame(card_img, bg="#FFFFFF")
        img_row.pack(fill="x")

        for thumb_txt in ["📦 Main", "🏷 Tag"]:
            box = tk.Label(img_row, text=thumb_txt, font=("Arial", 9), fg="#64748B", bg="#F1F5F9", width=8, height=4, bd=1, relief="solid")
            box.pack(side="left", padx=(0, 8))

        btn_plus = tk.Label(img_row, text="+", font=("Arial", 16, "bold"), fg="#2563EB", bg="#EFF6FF", width=4, height=2, bd=1, relief="solid", cursor="hand2")
        btn_plus.pack(side="left")

        # 2. Dimensions Card
        card_dim = tk.Frame(right_col, bg="#FFFFFF", bd=1, relief="solid", padx=16, pady=14)
        card_dim.pack(fill="x", pady=(0, 14))

        tk.Label(card_dim, text="Dimensions", font=("Arial", 12, "bold"), fg="#1E293B", bg="#FFFFFF").pack(anchor="w", pady=(0, 10))

        grid_dim = tk.Frame(card_dim, bg="#FFFFFF")
        grid_dim.pack(fill="x")
        grid_dim.columnconfigure(0, weight=1)
        grid_dim.columnconfigure(1, weight=1)
        grid_dim.columnconfigure(2, weight=1)

        self._add_field(grid_dim, "Width (cm)", "entry_w", "15", 0, 0)
        self._add_field(grid_dim, "Height (cm)", "entry_h", "20", 0, 1)
        self._add_field(grid_dim, "Length (cm)", "entry_l", "10", 0, 2)

        # 3. Inventory Control Card
        card_inv = tk.Frame(right_col, bg="#FFFFFF", bd=1, relief="solid", padx=16, pady=14)
        card_inv.pack(fill="x", pady=(0, 14))

        tk.Label(card_inv, text="Inventory Control", font=("Arial", 12, "bold"), fg="#1E293B", bg="#FFFFFF").pack(anchor="w", pady=(0, 8))

        tk.Label(card_inv, text="☑ Track Inventory for this product", font=("Arial", 9, "bold"), fg="#2563EB", bg="#FFFFFF").pack(anchor="w", pady=(0, 6))

        grid_ctrl = tk.Frame(card_inv, bg="#FFFFFF")
        grid_ctrl.pack(fill="x")
        grid_ctrl.columnconfigure(0, weight=1)
        grid_ctrl.columnconfigure(1, weight=1)

        self._add_field(grid_ctrl, "Opening Stock", "entry_open", "45", 0, 0)
        self._add_field(grid_ctrl, "Reorder Point", "entry_reorder", "12", 0, 1)

        # 4. Valuation Method Card
        card_val = tk.Frame(right_col, bg="#FFFFFF", bd=1, relief="solid", padx=16, pady=14)
        card_val.pack(fill="x")

        tk.Label(card_val, text="Inventory Valuation Method", font=("Arial", 12, "bold"), fg="#1E293B", bg="#FFFFFF").pack(anchor="w", pady=(0, 6))
        combo_val = ttk.Combobox(card_val, values=["FIFO (First In First Out)", "LIFO (Last In First Out)", "WAC (Weighted Average)"], state="readonly")
        combo_val.set("FIFO (First In First Out)")
        combo_val.pack(fill="x", pady=(0, 4))

    def _add_field(self, parent, label_txt, key, def_val, row, col, colspan=1):
        """Helper to create an elegant floating input field with focus highlight."""
        lbl = tk.Label(parent, text=label_txt, font=("Segoe UI", 9, "bold"), fg="#334155", bg="#FFFFFF")
        lbl.grid(row=row*2, column=col, columnspan=colspan, sticky="w", pady=(6, 2), padx=4)

        box = tk.Frame(parent, bg="#F8FAFC", highlightthickness=1, highlightbackground="#CBD5E1")
        box.grid(row=row*2 + 1, column=col, columnspan=colspan, sticky="ew", pady=(0, 6), padx=4)

        e = tk.Entry(
            box,
            font=("Segoe UI", 10),
            bg="#F8FAFC",
            fg="#0F172A",
            bd=0,
            relief="flat",
            highlightthickness=0,
            insertbackground="#028090"
        )
        e.pack(fill="both", expand=True, padx=8, pady=5)
        e.insert(0, def_val)

        def on_focus_in(event, b=box, entry=e):
            b.config(highlightbackground="#028090", highlightthickness=2, bg="#FFFFFF")
            entry.config(bg="#FFFFFF")

        def on_focus_out(event, b=box, entry=e):
            b.config(highlightbackground="#CBD5E1", highlightthickness=1, bg="#F8FAFC")
            entry.config(bg="#F8FAFC")

        e.bind("<FocusIn>", on_focus_in)
        e.bind("<FocusOut>", on_focus_out)
        self.entries[key] = e

    def reset_form(self):
        df_prod = self.storage.get_products()
        next_id = generate_next_id("PRD-", df_prod["product_id"].tolist() if not df_prod.empty else [])
        if "entry_id" in self.entries:
            self.entries["entry_id"].delete(0, tk.END)
            self.entries["entry_id"].insert(0, next_id)

    def _submit_create(self):
        pid = self.entries["entry_id"].get().strip()
        pname = self.entries["entry_name"].get().strip()
        cat = self.entries["combo_category"].get().strip()
        sid = self.entries["combo_supplier"].get().strip()
        c = self.entries["entry_cost"].get().strip()
        p = self.entries["entry_price"].get().strip()
        qty = self.entries["entry_stock"].get().strip()
        min_stk = self.entries["entry_min"].get().strip()
        exp = self.entries["entry_expiry"].get().strip()

        df_prod = self.storage.get_products()
        is_valid, msg, cleaned = validate_product_data(
            pid, pname, cat, sid, c, p, qty, min_stk, exp,
            existing_product_ids=df_prod["product_id"].tolist() if not df_prod.empty else []
        )
        if not is_valid:
            messagebox.showerror("Validation Error", msg)
            return

        ok, save_msg = self.storage.add_product(cleaned)
        if ok:
            messagebox.showinfo("Product Created", f"✓ {pname} ({pid}) successfully added to store catalog!")
            self.reset_form()
            self._navigate_to("op_read")
        else:
            messagebox.showerror("Error", save_msg)

    def _navigate_to(self, key):
        if self.nav_callback:
            self.nav_callback(key)


# =============================================================================
# 2. UPDATE PRODUCT VIEW (KANGAROO - OPERATION 3)
# =============================================================================

class UpdateProductView(ttk.Frame):
    """
    Operation 3: UPDATE – KANGAROO Edit / Update Product matching reference design.
    """

    def __init__(self, parent: tk.Widget, storage: StorageManager, nav_callback=None):
        super().__init__(parent)
        self.storage = storage
        self.nav_callback = nav_callback
        self.entries = {}

        self._build_ui()
        self.load_product_list()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Gradient backdrop (#F3EEF9 to #FCEFF2)
        canvas = tk.Canvas(self, bg="#F3EEF9", highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")

        # Central Modal Card
        self.form_card = tk.Frame(canvas, bg="#FFFFFF", bd=1, relief="solid", padx=28, pady=20)
        canvas.create_window(540, 360, window=self.form_card, anchor="center")

        def _on_resize(event):
            canvas.coords(1, event.width // 2, event.height // 2)
        canvas.bind("<Configure>", _on_resize)

        # 1. Header (KANGAROO Brand & Breadcrumb)
        hdr = tk.Frame(self.form_card, bg="#FFFFFF")
        hdr.pack(fill="x", pady=(0, 14))

        tk.Label(hdr, text="KANGAROO", font=("Arial", 12, "bold"), fg="#4F46E5", bg="#FFFFFF").pack(side="left")
        tk.Label(hdr, text="  Inventory  ›  Edit Product Details", font=("Arial", 10), fg="#94A3B8", bg="#FFFFFF").pack(side="left")

        if self.nav_callback:
            btn_back = tk.Button(
                hdr,
                text="← Back to Hub",
                font=("Arial", 9, "bold"),
                fg="#4F46E5",
                bg="#EEF2FF",
                relief="flat",
                command=lambda: self._navigate_to("hub")
            )
            btn_back.pack(side="right")

        # 2. Product Selector Bar
        sel_box = tk.Frame(self.form_card, bg="#F8FAFC", padx=12, pady=8, bd=1, relief="solid")
        sel_box.pack(fill="x", pady=(0, 14))

        tk.Label(sel_box, text="Select Product to Update:", font=("Arial", 10, "bold"), fg="#334155", bg="#F8FAFC").pack(side="left", padx=(0, 8))
        self.combo_select = ttk.Combobox(sel_box, state="readonly", width=42)
        self.combo_select.pack(side="left")
        self.combo_select.bind("<<ComboboxSelected>>", self._on_product_selected)

        # 3. Form Grid
        grid = tk.Frame(self.form_card, bg="#FFFFFF")
        grid.pack(fill="x", pady=(0, 14))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        fields = [
            ("Product Name*", "product_name", 0, 0),
            ("Category*", "category", 0, 1),
            ("SKU / Barcode*", "sku", 1, 0),
            ("Supplier ID*", "supplier_id", 1, 1),
            ("Purchase Price (₹)*", "purchase_price", 2, 0),
            ("Selling Price (₹)*", "selling_price", 2, 1),
            ("Current Stock Quantity*", "stock_quantity", 3, 0),
            ("Minimum Reorder Level*", "minimum_stock", 3, 1),
        ]

        for lbl_t, key, r, c in fields:
            lbl = tk.Label(grid, text=lbl_t, font=("Segoe UI", 9, "bold"), fg="#334155", bg="#FFFFFF")
            lbl.grid(row=r*2, column=c, sticky="w", pady=(5, 2), padx=6)
            box = tk.Frame(grid, bg="#F8FAFC", highlightthickness=1, highlightbackground="#CBD5E1")
            box.grid(row=r*2+1, column=c, sticky="ew", pady=(0, 6), padx=6)
            ent = tk.Entry(
                box,
                font=("Segoe UI", 10),
                bg="#F8FAFC",
                fg="#0F172A",
                bd=0,
                relief="flat",
                highlightthickness=0,
                insertbackground="#4F46E5"
            )
            ent.pack(fill="both", expand=True, padx=8, pady=5)
            
            def make_focus_handlers(b=box, e=ent):
                e.bind("<FocusIn>", lambda ev: (b.config(highlightbackground="#4F46E5", highlightthickness=2, bg="#FFFFFF"), e.config(bg="#FFFFFF")))
                e.bind("<FocusOut>", lambda ev: (b.config(highlightbackground="#CBD5E1", highlightthickness=1, bg="#F8FAFC"), e.config(bg="#F8FAFC")))
            make_focus_handlers()
            self.entries[key] = ent

        # Returnable Toggle Banner
        ret_box = tk.Frame(self.form_card, bg="#F8FAFC", padx=12, pady=6, bd=1, relief="solid")
        ret_box.pack(fill="x", pady=(0, 12))
        tk.Label(ret_box, text="☑ Is this product Returnable?", font=("Arial", 9, "bold"), fg="#4F46E5", bg="#F8FAFC").pack(side="left")
        tk.Label(ret_box, text="Standard 30-day customer warranty policy", font=("Arial", 9), fg="#94A3B8", bg="#F8FAFC").pack(side="right")

        # Dimensions & Weights Row
        dim_box = tk.Frame(self.form_card, bg="#FFFFFF")
        dim_box.pack(fill="x", pady=(0, 16))
        for i in range(4): dim_box.columnconfigure(i, weight=1)

        for idx, (dt, dv) in enumerate([("Weight (kg)", "0.5"), ("Height (cm)", "20"), ("Width (cm)", "15"), ("Length (cm)", "10")]):
            tk.Label(dim_box, text=dt, font=("Arial", 8, "bold"), fg="#64748B", bg="#FFFFFF").grid(row=0, column=idx, sticky="w", padx=4)
            de = tk.Entry(dim_box, font=("Arial", 9), bg="#F8FAFC", bd=1, relief="solid")
            de.grid(row=1, column=idx, sticky="ew", padx=4, pady=2)
            de.insert(0, dv)

        # 4. Action Buttons (Cancel, Apply, Edit Product)
        act_box = tk.Frame(self.form_card, bg="#FFFFFF")
        act_box.pack(fill="x")

        tk.Button(
            act_box,
            text="Cancel",
            font=("Arial", 10),
            fg="#64748B",
            bg="#FFFFFF",
            relief="solid",
            bd=1,
            padx=16,
            pady=4,
            command=lambda: self._navigate_to("hub")
        ).pack(side="right", padx=(6, 0))

        tk.Button(
            act_box,
            text="Apply Changes",
            font=("Arial", 10, "bold"),
            fg="#2563EB",
            bg="#EFF6FF",
            relief="solid",
            bd=1,
            padx=16,
            pady=4,
            command=self._submit_update
        ).pack(side="right", padx=(6, 0))

        tk.Button(
            act_box,
            text="Edit Product",
            font=("Arial", 10, "bold"),
            fg="#FFFFFF",
            bg="#2563EB",
            relief="flat",
            bd=0,
            padx=18,
            pady=4,
            command=self._submit_update
        ).pack(side="right")

    def load_product_list(self):
        df_prod = self.storage.get_products()
        if not df_prod.empty:
            opts = [f"{r['product_id']} - {r['product_name']}" for _, r in df_prod.iterrows()]
            self.combo_select["values"] = opts
            self.combo_select.set(opts[0])
            self._populate_fields(df_prod.iloc[0])

    def _on_product_selected(self, event=None):
        sel = self.combo_select.get()
        if not sel: return
        pid = sel.split(" - ")[0]
        df = self.storage.get_products()
        row = df[df["product_id"] == pid]
        if not row.empty:
            self._populate_fields(row.iloc[0])

    def _populate_fields(self, row):
        for k in ["product_name", "category", "supplier_id", "purchase_price", "selling_price", "stock_quantity", "minimum_stock"]:
            if k in self.entries:
                self.entries[k].delete(0, tk.END)
                self.entries[k].insert(0, str(row.get(k, "")))
        if "sku" in self.entries:
            self.entries["sku"].delete(0, tk.END)
            self.entries["sku"].insert(0, str(row.get("sku", row.get("product_id", ""))))

    def _submit_update(self):
        sel = self.combo_select.get()
        if not sel: return
        pid = sel.split(" - ")[0]

        updates = {
            "product_name": self.entries["product_name"].get().strip(),
            "category": self.entries["category"].get().strip(),
            "supplier_id": self.entries["supplier_id"].get().strip(),
            "purchase_price": self.entries["purchase_price"].get().strip(),
            "selling_price": self.entries["selling_price"].get().strip(),
            "stock_quantity": self.entries["stock_quantity"].get().strip(),
            "minimum_stock": self.entries["minimum_stock"].get().strip(),
        }

        ok, msg = self.storage.update_product(pid, updates)
        if ok:
            messagebox.showinfo("Success", f"Product {pid} updated successfully!")
            self.load_product_list()
        else:
            messagebox.showerror("Error", msg)

    def _navigate_to(self, key):
        if self.nav_callback:
            self.nav_callback(key)


# =============================================================================
# 3. DELETE PRODUCT VIEW (OPERATION 4 WITH CONFIRMATION MODAL)
# =============================================================================

class DeleteProductView(ttk.Frame):
    """
    Operation 4: DELETE – Safe Deletion Table with Floating Confirmation Modal.
    """

    def __init__(self, parent: tk.Widget, storage: StorageManager, nav_callback=None):
        super().__init__(parent)
        self.storage = storage
        self.nav_callback = nav_callback

        self._build_ui()
        self.load_products()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Main Table Container (#F8FAFC)
        container = tk.Frame(self, bg="#F1F5F9", padx=20, pady=16)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        # Top Bar
        top_bar = tk.Frame(container, bg="#FFFFFF", padx=16, pady=10, bd=1, relief="solid")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # Tabs: Products, Price Lists, Stock Adjustments
        tab_box = tk.Frame(top_bar, bg="#FFFFFF")
        tab_box.pack(side="left")

        for tab_t, is_act in [("Products", True), ("Price Lists", False), ("Stock Adjustments", False)]:
            col = "#2563EB" if is_act else "#64748B"
            bgc = "#EFF6FF" if is_act else "#FFFFFF"
            tk.Label(tab_box, text=tab_t, font=("Arial", 10, "bold" if is_act else "normal"), fg=col, bg=bgc, padx=12, pady=4).pack(side="left", padx=2)

        # Right Actions
        act_box = tk.Frame(top_bar, bg="#FFFFFF")
        act_box.pack(side="right")

        if self.nav_callback:
            tk.Button(
                act_box,
                text="← Back to Hub",
                font=("Arial", 9, "bold"),
                fg="#475569",
                bg="#F1F5F9",
                relief="flat",
                command=lambda: self._navigate_to("hub")
            ).pack(side="left", padx=(0, 10))

        btn_trigger_del = tk.Button(
            act_box,
            text="🗑️ Delete Selected Product",
            font=("Arial", 10, "bold"),
            fg="#FFFFFF",
            bg="#E11D48",
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2",
            command=self._execute_delete
        )
        btn_trigger_del.pack(side="left")

        # Table Card
        table_frame = tk.Frame(container, bg="#FFFFFF", bd=1, relief="solid")
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = ("select", "name", "price", "cost", "unit", "stock", "val")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)

        headers = [
            ("select", "☐", 40),
            ("name", "Name & Description", 260),
            ("price", "Selling Price (₹)", 105),
            ("cost", "Cost Price (₹)", 105),
            ("unit", "Unit", 80),
            ("stock", "Stock In Hand", 100),
            ("val", "Stock Value (₹)", 115),
        ]

        for cid, ctext, cwidth in headers:
            self.tree.heading(cid, text=ctext)
            self.tree.column(cid, width=cwidth, anchor="center" if cid in ("select", "unit", "stock") else "w")

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

    def load_products(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        df = self.storage.get_products()
        for _, r in df.iterrows():
            pid = str(r["product_id"])
            pname = str(r["product_name"])
            sp = safe_float(r.get("selling_price", 0.0))
            cp = safe_float(r.get("purchase_price", 0.0))
            stk = safe_int(r.get("stock_quantity", 0))
            val = stk * sp

            self.tree.insert("", "end", values=(
                "☐",
                f"{pname} ({pid})",
                f"₹{sp:.2f}",
                f"₹{cp:.2f}",
                "Pcs",
                stk,
                f"₹{val:.2f}"
            ))

    def _execute_delete(self):
        """Opens the exact floating Delete Product confirmation modal matching reference."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a product from the list to delete.", parent=self)
            return

        values = self.tree.item(selected[0], "values")
        full_name = values[1]
        pid = full_name.split("(")[-1].replace(")", "").strip() if "(" in full_name else full_name

        # Floating Delete Modal matching reference design
        dlg = tk.Toplevel(self)
        dlg.title("Delete Product")
        dlg.geometry("380x230")
        dlg.resizable(False, False)
        dlg.configure(bg="#FFFFFF")
        dlg.transient(self)
        dlg.grab_set()

        # Center Dialog over Parent
        dlg.geometry("+%d+%d" % (self.winfo_rootx() + 250, self.winfo_rooty() + 180))

        inner = tk.Frame(dlg, bg="#FFFFFF", padx=24, pady=20)
        inner.pack(fill="both", expand=True)

        # Red Warning Icon in circle
        icon_box = tk.Label(
            inner,
            text="⚠️",
            font=("Arial", 18),
            fg="#E11D48",
            bg="#FFE4E6",
            width=3,
            height=1
        )
        icon_box.pack(pady=(0, 10))

        # Title: 'Delete product'
        tk.Label(
            inner,
            text="Delete product",
            font=("Arial", 14, "bold"),
            fg="#1E293B",
            bg="#FFFFFF"
        ).pack(pady=(0, 6))

        # Subtitle: 'Are you sure you want to delete this product? This action cannot be undone.'
        tk.Label(
            inner,
            text=f"Are you sure you want to delete '{full_name}'?\nThis action cannot be undone.",
            font=("Arial", 10),
            fg="#64748B",
            bg="#FFFFFF",
            justify="center"
        ).pack(pady=(0, 18))

        # Action Buttons: Cancel and Delete
        btn_box = tk.Frame(inner, bg="#FFFFFF")
        btn_box.pack(fill="x")

        def perform_delete():
            ok, msg = self.storage.delete_product(pid)
            dlg.destroy()
            if ok:
                messagebox.showinfo("Deleted", f"✓ Product '{pid}' successfully removed.", parent=self)
                self.load_products()
            else:
                messagebox.showerror("Error", msg, parent=self)

        tk.Button(
            btn_box,
            text="Cancel",
            font=("Arial", 10),
            fg="#475569",
            bg="#FFFFFF",
            relief="solid",
            bd=1,
            padx=20,
            pady=5,
            cursor="hand2",
            command=dlg.destroy
        ).pack(side="left", expand=True, padx=(0, 6))

        tk.Button(
            btn_box,
            text="Delete",
            font=("Arial", 10, "bold"),
            fg="#FFFFFF",
            bg="#E11D48",
            activebackground="#BE123C",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=22,
            pady=5,
            cursor="hand2",
            command=perform_delete
        ).pack(side="right", expand=True, padx=(6, 0))

    def _navigate_to(self, key):
        if self.nav_callback:
            self.nav_callback(key)


# =============================================================================
# STANDALONE FOUR OPERATIONS LAUNCHER
# =============================================================================

class StandaloneOperationsApp(tk.Tk):
    """
    Dedicated Standalone Window displaying the Four Independent Operation Pages:
    1. Create (Add new products)
    2. Retrieve (View and search products)
    3. Update (Modify product details)
    4. Delete (Remove products safely)
    """

    def __init__(self):
        super().__init__()
        self.title("Four Independent Operation Pages | Store Management")
        self.geometry("1280x820")
        self.configure(bg="#0B0F12")

        self.storage = StorageManager(auto_init=True)
        self._build_carousel_ui()

    def _build_carousel_ui(self):
        # Top Header Bar
        hdr = tk.Frame(self, bg="#0B0F12", padx=20, pady=12)
        hdr.pack(side="top", fill="x")

        tk.Label(hdr, text="Four Independent Operation Pages", font=("Arial", 16, "bold"), fg="#FFFFFF", bg="#0B0F12").pack(side="left")

        # Operation Switcher Tabs
        tabs_box = tk.Frame(hdr, bg="#0B0F12")
        tabs_box.pack(side="right")

        self.views = {
            "1. Create (Add new products)": CreateProductView,
            "2. Update (Modify details)": UpdateProductView,
            "3. Delete (Remove safely)": DeleteProductView,
        }

        self.active_btn = None
        self.current_view = None
        self.container = tk.Frame(self, bg="#F8FAFC")
        self.container.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        for name, cls in self.views.items():
            b = tk.Button(
                tabs_box,
                text=name,
                font=("Arial", 10, "bold"),
                fg="#94A3B8",
                bg="#1E293B",
                relief="flat",
                padx=12,
                pady=4,
                cursor="hand2"
            )
            b.configure(command=lambda n=name, c=cls, btn=b: self._switch_view(n, c, btn))
            b.pack(side="left", padx=4)
            if self.active_btn is None:
                self.active_btn = b

        first_name = list(self.views.keys())[0]
        self._switch_view(first_name, self.views[first_name], self.active_btn)

    def _switch_view(self, name, cls, btn):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = cls(self.container, self.storage)
        self.current_view.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = StandaloneOperationsApp()
    app.mainloop()
