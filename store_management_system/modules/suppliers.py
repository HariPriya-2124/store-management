"""
Supplier Management Module for Store Management System.
Implements supplier records viewing, addition, editing, safe referential-integrity
protected deletion, and inspection of products associated with each supplier.
"""

from datetime import date
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
from utils.helpers import export_dataframe_to_csv, generate_next_id
from utils.logger import get_logger
from utils.validators import validate_supplier_data

logger = get_logger("SupplierModule")


class SupplierManagementView(ttk.Frame):
    """
    Supplier Management View with Table, Searching, CRUD Modals,
    and Linked Product Relationship Viewer.
    """

    def __init__(self, parent: tk.Widget, storage: StorageManager, nav_callback=None):
        super().__init__(parent)
        self.storage = storage
        self.nav_callback = nav_callback

        self._build_ui()
        self.load_suppliers()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # 1. Top Header & Action Bar
        top_frame = tk.Frame(self, bg=THEME["gray_bg"])
        top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 8))

        lbl_title = tk.Label(
            top_frame,
            text="Supplier Management",
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
                relief="flat", padx=10, pady=3, cursor="hand2",
            ).pack(side="left", padx=(12, 0))

        actions_frame = tk.Frame(top_frame, bg=THEME["gray_bg"])
        actions_frame.pack(side="right")

        btn_add = tk.Button(
            actions_frame,
            text="➕ Add New Supplier",
            command=self._open_add_supplier_modal,
            bg=THEME["navy_accent"],
            fg=THEME["white"],
            font=FONTS["caption_bold"],
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
        )
        btn_add.pack(side="left", padx=4)

        btn_export = tk.Button(
            actions_frame,
            text="📥 Export CSV",
            command=self._export_suppliers_csv,
            bg=THEME["white"],
            fg=THEME["navy_accent"],
            bd=1,
            relief="solid",
            font=FONTS["caption_bold"],
            padx=10,
            pady=4,
            cursor="hand2",
        )
        btn_export.pack(side="left", padx=4)

        # 2. Search Bar
        filter_bar = tk.Frame(self, bg=THEME["white"], bd=1, relief="solid", padx=12, pady=8)
        filter_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        tk.Label(filter_bar, text="🔍 Search Suppliers:", font=FONTS["body_bold"], bg=THEME["white"], fg=THEME["text_secondary"]).pack(side="left", padx=(0, 5))
        self.entry_search = ttk.Entry(filter_bar, width=32)
        self.entry_search.pack(side="left", padx=(0, 15))
        self.entry_search.bind("<KeyRelease>", lambda e: self.filter_suppliers())

        btn_clear = tk.Button(
            filter_bar,
            text="Clear",
            command=lambda: (self.entry_search.delete(0, tk.END), self.filter_suppliers()),
            bg=THEME["gray_bg"],
            relief="flat",
            font=FONTS["caption"],
            padx=8,
            pady=2,
            cursor="hand2",
        )
        btn_clear.pack(side="left", padx=5)

        self.lbl_count = tk.Label(filter_bar, text="", font=FONTS["caption_bold"], bg=THEME["white"], fg=THEME["text_muted"])
        self.lbl_count.pack(side="right")

        # 3. Suppliers Data Table
        table_frame = tk.Frame(self, bg=THEME["white"], bd=1, relief="solid")
        table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = ("supplier_id", "supplier_name", "product_category", "contact_number", "email", "address", "linked_products")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        headers = {
            "supplier_id": ("Supplier ID", 90, "center"),
            "supplier_name": ("Company / Supplier Name", 220, "w"),
            "product_category": ("Category", 130, "w"),
            "contact_number": ("Contact Phone", 120, "center"),
            "email": ("Email Address", 180, "w"),
            "address": ("Physical Address", 230, "w"),
            "linked_products": ("Products", 80, "center"),
        }

        for col, (text, width, anchor) in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor)

        sb_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        sb_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        # 4. Context Operations
        btm_bar = tk.Frame(self, bg=THEME["gray_bg"])
        btm_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))

        btn_view_prods = tk.Button(
            btm_bar,
            text="📦 View Associated Products",
            command=self._view_linked_products,
            bg=THEME["navy_primary"],
            fg=THEME["white"],
            font=FONTS["caption_bold"],
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
        )
        btn_view_prods.pack(side="left", padx=(0, 6))

        btn_edit = tk.Button(
            btm_bar,
            text="✏️ Edit Selected",
            command=self._open_edit_supplier_modal,
            bg=THEME["navy_accent"],
            fg=THEME["white"],
            font=FONTS["caption_bold"],
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
        )
        btn_edit.pack(side="left", padx=6)

        btn_del = tk.Button(
            btm_bar,
            text="🗑️ Delete Selected",
            command=self._delete_selected_supplier,
            bg=THEME["danger"],
            fg=THEME["white"],
            font=FONTS["caption_bold"],
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
        )
        btn_del.pack(side="left", padx=6)

    def load_suppliers(self):
        """Reloads supplier datasets and updates table."""
        self.df_suppliers = self.storage.get_suppliers()
        self.df_products = self.storage.get_products()
        self.filter_suppliers()

    def filter_suppliers(self):
        """Filters suppliers table by search input."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.df_suppliers.empty:
            self.lbl_count.config(text="0 suppliers")
            return

        df = self.df_suppliers.copy()
        query = self.entry_search.get().strip().lower()

        if query:
            df = df[
                df["supplier_id"].str.lower().str.contains(query, na=False)
                | df["supplier_name"].str.lower().str.contains(query, na=False)
                | df["product_category"].str.lower().str.contains(query, na=False)
                | df["email"].str.lower().str.contains(query, na=False)
            ]

        # Calculate linked product count per supplier
        prod_counts = {}
        if not self.df_products.empty and "supplier_id" in self.df_products.columns:
            prod_counts = self.df_products["supplier_id"].value_counts().to_dict()

        for _, row in df.iterrows():
            sid = row["supplier_id"]
            cnt = prod_counts.get(sid, 0)
            self.tree.insert(
                "",
                "end",
                values=(
                    sid,
                    row["supplier_name"],
                    row["product_category"],
                    row["contact_number"],
                    row["email"],
                    row["address"],
                    f"{cnt} items",
                ),
            )

        self.lbl_count.config(text=f"Showing {len(df)} of {len(self.df_suppliers)} suppliers")

    # =========================================================================
    # VIEW LINKED PRODUCTS
    # =========================================================================

    def _view_linked_products(self):
        """Displays modal listing all products supplied by the selected supplier."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a supplier to view their supplied products.")
            return

        values = self.tree.item(selected[0], "values")
        sid = values[0]
        sname = values[1]

        linked_df = self.storage.get_supplier_products(sid)

        modal = tk.Toplevel(self)
        modal.title(f"Supplied Products: {sname} ({sid})")
        modal.geometry("700x420")
        modal.transient(self.winfo_toplevel())

        tk.Label(modal, text=f"Products from {sname}", font=FONTS["h2"], fg=THEME["navy_primary"]).pack(pady=(12, 4))
        tk.Label(modal, text=f"Supplier ID: {sid} | Total Linked Products: {len(linked_df)}", font=FONTS["caption"], fg=THEME["text_muted"]).pack(pady=(0, 10))

        frame = tk.Frame(modal, padx=15, pady=5)
        frame.pack(fill="both", expand=True)

        cols = ("id", "name", "category", "cost", "retail", "stock")
        tree_prods = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        tree_prods.heading("id", text="Product ID")
        tree_prods.heading("name", text="Product Name")
        tree_prods.heading("category", text="Category")
        tree_prods.heading("cost", text="Cost (₹)")
        tree_prods.heading("retail", text="Retail (₹)")
        tree_prods.heading("stock", text="Stock")

        tree_prods.column("id", width=80, anchor="center")
        tree_prods.column("name", width=220, anchor="w")
        tree_prods.column("category", width=120, anchor="w")
        tree_prods.column("cost", width=80, anchor="e")
        tree_prods.column("retail", width=80, anchor="e")
        tree_prods.column("stock", width=70, anchor="center")

        sb = ttk.Scrollbar(frame, orient="vertical", command=tree_prods.yview)
        tree_prods.configure(yscrollcommand=sb.set)
        tree_prods.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        if not linked_df.empty:
            for _, r in linked_df.iterrows():
                tree_prods.insert("", "end", values=(
                    r["product_id"],
                    r["product_name"],
                    r["category"],
                    f"₹{float(r['purchase_price']):.2f}",
                    f"₹{float(r['selling_price']):.2f}",
                    r["stock_quantity"]
                ))
        else:
            tk.Label(modal, text="No products are currently associated with this supplier.", font=FONTS["body"], fg=THEME["text_muted"]).pack(pady=10)

        tk.Button(modal, text="Close", command=modal.destroy, font=FONTS["caption_bold"], padx=15, pady=4).pack(pady=10)

    # =========================================================================
    # ADD SUPPLIER MODAL
    # =========================================================================

    def _open_add_supplier_modal(self):
        """Modal dialog to register a new supplier."""
        modal = tk.Toplevel(self)
        modal.title("Add New Supplier")
        modal.geometry("500x450")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        next_sid = generate_next_id("SUP-", self.df_suppliers["supplier_id"].tolist() if not self.df_suppliers.empty else [], pad_length=3)

        tk.Label(modal, text="New Supplier Profile", font=FONTS["h2"], fg=THEME["navy_primary"]).pack(pady=(15, 10))

        form = tk.Frame(modal, padx=25)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        fields = [
            ("Supplier ID:", next_sid),
            ("Company Name:", ""),
            ("Contact Number:", "+1-555-0199"),
            ("Email Address:", "info@newsupplier.com"),
            ("Physical Address:", "123 Supply Route, Metro City"),
            ("Product Category:", "General Pantry"),
        ]

        entries = {}
        for row_idx, (label, def_val) in enumerate(fields):
            tk.Label(form, text=label, font=FONTS["body_bold"], anchor="w").grid(row=row_idx, column=0, sticky="w", pady=7)
            entry = ttk.Entry(form)
            entry.insert(0, def_val)
            entry.grid(row=row_idx, column=1, sticky="ew", padx=(10, 0), pady=7)
            entries[label] = entry

        def save():
            sid = entries["Supplier ID:"].get()
            sname = entries["Company Name:"].get()
            contact = entries["Contact Number:"].get()
            email = entries["Email Address:"].get()
            addr = entries["Physical Address:"].get()
            cat = entries["Product Category:"].get()

            is_valid, msg, cleaned = validate_supplier_data(
                sid, sname, contact, email, addr, cat,
                existing_supplier_ids=self.df_suppliers["supplier_id"].tolist() if not self.df_suppliers.empty else []
            )
            if not is_valid:
                messagebox.showerror("Validation Error", msg, parent=modal)
                return

            ok, save_msg = self.storage.add_supplier(cleaned)
            if ok:
                messagebox.showinfo("Success", save_msg, parent=modal)
                modal.destroy()
                self.load_suppliers()
            else:
                messagebox.showerror("Error", save_msg, parent=modal)

        btn_box = tk.Frame(modal, pady=15)
        btn_box.pack(fill="x")
        tk.Button(btn_box, text="Cancel", command=modal.destroy, font=FONTS["caption"], padx=10, pady=4).pack(side="right", padx=10)
        tk.Button(btn_box, text="Save Supplier", command=save, bg=THEME["navy_accent"], fg=THEME["white"], font=FONTS["caption_bold"], relief="flat", padx=14, pady=4).pack(side="right")

    # =========================================================================
    # EDIT SUPPLIER MODAL
    # =========================================================================

    def _open_edit_supplier_modal(self):
        """Modal dialog to edit selected supplier."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a supplier from the table to edit.")
            return

        values = self.tree.item(selected[0], "values")
        sid = values[0]
        supp_row = self.df_suppliers[self.df_suppliers["supplier_id"] == sid].iloc[0]

        modal = tk.Toplevel(self)
        modal.title(f"Edit Supplier - {sid}")
        modal.geometry("500x450")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        tk.Label(modal, text=f"Update Supplier: {sid}", font=FONTS["h2"], fg=THEME["navy_primary"]).pack(pady=(15, 10))

        form = tk.Frame(modal, padx=25)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        fields = [
            ("Company Name:", supp_row["supplier_name"]),
            ("Contact Number:", supp_row["contact_number"]),
            ("Email Address:", supp_row["email"]),
            ("Physical Address:", supp_row["address"]),
            ("Product Category:", supp_row["product_category"]),
        ]

        entries = {}
        for row_idx, (label, val) in enumerate(fields):
            tk.Label(form, text=label, font=FONTS["body_bold"], anchor="w").grid(row=row_idx, column=0, sticky="w", pady=7)
            entry = ttk.Entry(form)
            entry.insert(0, str(val))
            entry.grid(row=row_idx, column=1, sticky="ew", padx=(10, 0), pady=7)
            entries[label] = entry

        def update():
            sname = entries["Company Name:"].get()
            contact = entries["Contact Number:"].get()
            email = entries["Email Address:"].get()
            addr = entries["Physical Address:"].get()
            cat = entries["Product Category:"].get()

            is_valid, msg, cleaned = validate_supplier_data(
                sid, sname, contact, email, addr, cat,
                existing_supplier_ids=[], is_update=True
            )
            if not is_valid:
                messagebox.showerror("Validation Error", msg, parent=modal)
                return

            ok, save_msg = self.storage.update_supplier(sid, cleaned)
            if ok:
                messagebox.showinfo("Success", save_msg, parent=modal)
                modal.destroy()
                self.load_suppliers()
            else:
                messagebox.showerror("Error", save_msg, parent=modal)

        btn_box = tk.Frame(modal, pady=15)
        btn_box.pack(fill="x")
        tk.Button(btn_box, text="Cancel", command=modal.destroy, font=FONTS["caption"], padx=10, pady=4).pack(side="right", padx=10)
        tk.Button(btn_box, text="Save Changes", command=update, bg=THEME["navy_accent"], fg=THEME["white"], font=FONTS["caption_bold"], relief="flat", padx=14, pady=4).pack(side="right")

    # =========================================================================
    # DELETE SUPPLIER (REFERENTIAL INTEGRITY PROTECTED)
    # =========================================================================

    def _delete_selected_supplier(self):
        """Safely deletes supplier, guarding against foreign key deletion."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a supplier to delete.")
            return

        values = self.tree.item(selected[0], "values")
        sid = values[0]
        sname = values[1]

        # First check if products are linked
        linked_df = self.storage.get_supplier_products(sid)
        if not linked_df.empty:
            messagebox.showerror(
                "Deletion Blocked",
                f"Cannot delete supplier '{sname}' ({sid})!\n\n"
                f"There are {len(linked_df)} product(s) currently referencing this supplier:\n"
                f"{', '.join(linked_df['product_id'].tolist()[:5])}{'...' if len(linked_df) > 5 else ''}\n\n"
                "To maintain data integrity, you must reassign or remove those products before deleting this supplier."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Supplier Deletion",
            f"Are you sure you want to permanently delete supplier '{sname}' ({sid})?\n\n"
            "An automatic pre-deletion safety backup will be created.",
            icon="warning"
        )
        if not confirm:
            return

        ok, msg = self.storage.delete_supplier(sid)
        if ok:
            messagebox.showinfo("Deleted", msg)
            self.load_suppliers()
        else:
            messagebox.showerror("Error", msg)

    # =========================================================================
    # EXPORT CSV
    # =========================================================================

    def _export_suppliers_csv(self):
        """Exports currently loaded suppliers table to CSV."""
        if self.df_suppliers.empty:
            messagebox.showinfo("Export", "No supplier records available to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"suppliers_export_{date.today().strftime('%Y%m%d')}.csv"
        )
        if not file_path:
            return

        ok, msg = export_dataframe_to_csv(self.df_suppliers, file_path)
        if ok:
            messagebox.showinfo("Export Complete", msg)
        else:
            messagebox.showerror("Export Failed", msg)

