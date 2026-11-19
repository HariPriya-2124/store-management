"""
Analytics & Data Science Module for Store Management System.
Leverages Pandas, NumPy, and Matplotlib to provide business intelligence,
sales forecasting insights, inventory turnover metrics, and visual reporting.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import FONTS, THEME
from database.storage_manager import StorageManager
from utils.helpers import format_currency, format_quantity, safe_float, safe_int
from utils.logger import get_logger

logger = get_logger("Analytics")


# =============================================================================
# DATA SCIENCE CALCULATION FUNCTIONS (PANDAS & NUMPY)
# =============================================================================

def compute_kpis(storage: StorageManager) -> dict:
    """
    Computes key performance indicators across all datasets.
    """
    df_prod = storage.get_products()
    df_supp = storage.get_suppliers()
    df_sales = storage.get_sales()
    df_exp = storage.get_expiry_alerts()

    # 1. Total Products & Suppliers
    total_products = len(df_prod) if not df_prod.empty else 0
    total_suppliers = len(df_supp) if not df_supp.empty else 0

    # 2. Total Stock Units & Valuations
    total_stock_units = 0
    total_inventory_cost = 0.0
    total_inventory_retail = 0.0
    low_stock_count = 0

    if not df_prod.empty:
        stock_q = pd.to_numeric(df_prod["stock_quantity"], errors="coerce").fillna(0)
        p_price = pd.to_numeric(df_prod["purchase_price"], errors="coerce").fillna(0.0)
        s_price = pd.to_numeric(df_prod["selling_price"], errors="coerce").fillna(0.0)
        min_stock = pd.to_numeric(df_prod["minimum_stock"], errors="coerce").fillna(0)

        total_stock_units = int(stock_q.sum())
        total_inventory_cost = float((stock_q * p_price).sum())
        total_inventory_retail = float((stock_q * s_price).sum())
        low_stock_count = int((stock_q <= min_stock).sum())

    # 3. Sales & Revenue
    total_revenue = 0.0
    total_units_sold = 0
    total_transactions = len(df_sales) if not df_sales.empty else 0
    avg_order_value = 0.0

    if not df_sales.empty:
        tot_amt = pd.to_numeric(df_sales["total_amount"], errors="coerce").fillna(0.0)
        sq = pd.to_numeric(df_sales["quantity"], errors="coerce").fillna(0)
        total_revenue = float(tot_amt.sum())
        total_units_sold = int(sq.sum())
        if total_transactions > 0:
            avg_order_value = total_revenue / total_transactions

    # 4. Expiry Counts
    expired_count = 0
    expiring_soon_count = 0  # within 7 days
    expiring_caution_count = 0  # 8-30 days

    if not df_exp.empty:
        days = pd.to_numeric(df_exp["days_until_expiry"], errors="coerce").fillna(999)
        expired_count = int((days <= 0).sum())
        expiring_soon_count = int(((days > 0) & (days <= 7)).sum())
        expiring_caution_count = int(((days > 7) & (days <= 30)).sum())

    return {
        "total_products": total_products,
        "total_suppliers": total_suppliers,
        "total_stock_units": total_stock_units,
        "total_inventory_cost": total_inventory_cost,
        "total_inventory_retail": total_inventory_retail,
        "potential_profit": total_inventory_retail - total_inventory_cost,
        "total_revenue": total_revenue,
        "total_units_sold": total_units_sold,
        "total_transactions": total_transactions,
        "avg_order_value": avg_order_value,
        "low_stock_count": low_stock_count,
        "expired_count": expired_count,
        "expiring_soon_count": expiring_soon_count,
        "expiring_caution_count": expiring_caution_count,
    }


def get_sales_trend_data(storage: StorageManager, days_window: int = 60) -> pd.DataFrame:
    """
    Returns time-series sales aggregate (Date, Daily Revenue, Units Sold, Transaction Count).
    """
    df_sales = storage.get_sales()
    if df_sales.empty:
        return pd.DataFrame(columns=["sale_date", "revenue", "quantity", "tx_count"])

    df = df_sales.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0.0)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)

    # Filter by date window if specified
    if days_window > 0:
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days_window)
        df = df[df["sale_date"] >= cutoff]

    grouped = df.groupby(df["sale_date"].dt.strftime("%Y-%m-%d")).agg(
        revenue=("total_amount", "sum"),
        quantity=("quantity", "sum"),
        tx_count=("transaction_id", "count")
    ).reset_index().sort_values("sale_date")

    return grouped


def get_category_analytics(storage: StorageManager) -> pd.DataFrame:
    """
    Analyzes revenue, product count, and inventory stock across categories.
    """
    df_prod = storage.get_products()
    df_sales = storage.get_sales()

    if df_prod.empty:
        return pd.DataFrame(columns=["category", "product_count", "stock_units", "inventory_cost", "revenue"])

    df_p = df_prod.copy()
    df_p["stock_quantity"] = pd.to_numeric(df_p["stock_quantity"], errors="coerce").fillna(0)
    df_p["purchase_price"] = pd.to_numeric(df_p["purchase_price"], errors="coerce").fillna(0.0)
    df_p["inv_val"] = df_p["stock_quantity"] * df_p["purchase_price"]

    cat_prod = df_p.groupby("category").agg(
        product_count=("product_id", "count"),
        stock_units=("stock_quantity", "sum"),
        inventory_cost=("inv_val", "sum")
    ).reset_index()

    if not df_sales.empty:
        merged = df_sales.merge(df_p[["product_id", "category"]], on="product_id", how="left")
        merged["total_amount"] = pd.to_numeric(merged["total_amount"], errors="coerce").fillna(0.0)
        cat_rev = merged.groupby("category")["total_amount"].sum().reset_index()
        cat_rev.rename(columns={"total_amount": "revenue"}, inplace=True)
        final_df = cat_prod.merge(cat_rev, on="category", how="left").fillna(0.0)
    else:
        cat_prod["revenue"] = 0.0
        final_df = cat_prod

    return final_df.sort_values("revenue", ascending=False)


def get_product_sales_ranking(storage: StorageManager) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (best_selling_df, least_selling_df) with unit volume, revenue, and gross profit.
    """
    df_prod = storage.get_products()
    df_sales = storage.get_sales()

    if df_prod.empty:
        cols = ["product_id", "product_name", "category", "units_sold", "revenue", "gross_profit"]
        return pd.DataFrame(columns=cols), pd.DataFrame(columns=cols)

    df_p = df_prod.copy()
    df_p["purchase_price"] = pd.to_numeric(df_p["purchase_price"], errors="coerce").fillna(0.0)
    df_p["selling_price"] = pd.to_numeric(df_p["selling_price"], errors="coerce").fillna(0.0)

    if df_sales.empty:
        df_p["units_sold"] = 0
        df_p["revenue"] = 0.0
        df_p["gross_profit"] = 0.0
        cols = ["product_id", "product_name", "category", "units_sold", "revenue", "gross_profit"]
        return df_p[cols].head(5), df_p[cols].head(5)

    df_s = df_sales.copy()
    df_s["quantity"] = pd.to_numeric(df_s["quantity"], errors="coerce").fillna(0)
    df_s["total_amount"] = pd.to_numeric(df_s["total_amount"], errors="coerce").fillna(0.0)

    sales_agg = df_s.groupby("product_id").agg(
        units_sold=("quantity", "sum"),
        revenue=("total_amount", "sum")
    ).reset_index()

    merged = df_p.merge(sales_agg, on="product_id", how="left")
    merged["units_sold"] = merged["units_sold"].fillna(0).astype(int)
    merged["revenue"] = merged["revenue"].fillna(0.0)
    merged["cogs"] = merged["units_sold"] * merged["purchase_price"]
    merged["gross_profit"] = merged["revenue"] - merged["cogs"]

    cols = ["product_id", "product_name", "category", "units_sold", "revenue", "gross_profit"]
    ranked_best = merged[cols].sort_values(by=["units_sold", "revenue"], ascending=[False, False]).reset_index(drop=True)
    ranked_least = merged[cols].sort_values(by=["units_sold", "revenue"], ascending=[True, True]).reset_index(drop=True)

    return ranked_best, ranked_least


# =============================================================================
# ANALYTICS GUI VIEW
# =============================================================================

class AnalyticsView(ttk.Frame):
    """
    Comprehensive Analytics and Data Science Dashboard View.
    Displays financial indicators, interactive charts, and product performance tables.
    """

    def __init__(self, parent: tk.Widget, storage: StorageManager, nav_callback=None):
        super().__init__(parent)
        self.storage = storage
        self.nav_callback = nav_callback
        self.selected_window = tk.IntVar(value=60)

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # Configure grid expansion
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # 1. Header & Filter Bar
        header_frame = tk.Frame(self, bg=THEME["gray_bg"])
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        title_lbl = tk.Label(
            header_frame,
            text="Analytics & Data Science Insights",
            font=FONTS["h1"],
            bg=THEME["gray_bg"],
            fg=THEME["text_primary"],
        )
        title_lbl.pack(side="left")

        # Back to hub button
        if self.nav_callback:
            tk.Button(
                header_frame,
                text="← Back to CRUD Operations",
                command=lambda: self.nav_callback("hub"),
                bg=THEME.get("turquoise", "#028090"),
                fg=THEME["white"],
                font=FONTS["caption_bold"],
                relief="flat", padx=10, pady=3, cursor="hand2",
            ).pack(side="left", padx=(12, 0))

        filter_frame = tk.Frame(header_frame, bg=THEME["gray_bg"])
        filter_frame.pack(side="right")

        tk.Label(
            filter_frame,
            text="Time Window:",
            font=FONTS["body_bold"],
            bg=THEME["gray_bg"],
            fg=THEME["text_secondary"]
        ).pack(side="left", padx=(0, 6))

        for text, days in [("Last 7 Days", 7), ("Last 30 Days", 30), ("Last 60 Days", 60), ("All Time", 0)]:
            r = tk.Radiobutton(
                filter_frame,
                text=text,
                variable=self.selected_window,
                value=days,
                command=self.refresh_data,
                bg=THEME["gray_bg"],
                activebackground=THEME["gray_bg"],
                font=FONTS["caption"],
            )
            r.pack(side="left", padx=4)

        export_btn = tk.Button(
            filter_frame,
            text="📊 Export Analytics CSV",
            command=self._export_analytics_report,
            bg=THEME["navy_accent"],
            fg=THEME["white"],
            font=FONTS["caption_bold"],
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
        )
        export_btn.pack(side="left", padx=(10, 0))

        # 2. Key Financial Indicators Frame
        self.kpi_container = tk.Frame(self, bg=THEME["gray_bg"])
        self.kpi_container.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        for col_idx in range(6):
            self.kpi_container.columnconfigure(col_idx, weight=1)

        # 3. Scrollable Main Content Notebook / Panes
        notebook = ttk.Notebook(self)
        notebook.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 15))

        # Tab 1: Visual Charts
        self.tab_charts = ttk.Frame(notebook)
        notebook.add(self.tab_charts, text=" Visual Dashboards & Trends ")

        # Tab 2: Best & Least Selling Tables
        self.tab_tables = ttk.Frame(notebook)
        notebook.add(self.tab_tables, text=" Product Performance Rankings ")

        self._build_charts_tab()
        self._build_tables_tab()

    def _build_charts_tab(self):
        """Constructs embedded Matplotlib visualizations."""
        self.tab_charts.columnconfigure(0, weight=1)
        self.tab_charts.columnconfigure(1, weight=1)
        self.tab_charts.rowconfigure(0, weight=1)
        self.tab_charts.rowconfigure(1, weight=1)

        # Chart 1: Sales Trend
        self.fig_sales = Figure(figsize=(5.5, 2.7), dpi=100)
        self.ax_sales = self.fig_sales.add_subplot(111)
        self.canvas_sales = FigureCanvasTkAgg(self.fig_sales, master=self.tab_charts)
        self.canvas_sales.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Chart 2: Category Distribution
        self.fig_cat = Figure(figsize=(5.5, 2.7), dpi=100)
        self.ax_cat = self.fig_cat.add_subplot(111)
        self.canvas_cat = FigureCanvasTkAgg(self.fig_cat, master=self.tab_charts)
        self.canvas_cat.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Chart 3: Top Selling
        self.fig_top = Figure(figsize=(5.5, 2.7), dpi=100)
        self.ax_top = self.fig_top.add_subplot(111)
        self.canvas_top = FigureCanvasTkAgg(self.fig_top, master=self.tab_charts)
        self.canvas_top.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Chart 4: Inventory & Expiry Risk Status
        self.fig_risk = Figure(figsize=(5.5, 2.7), dpi=100)
        self.ax_risk = self.fig_risk.add_subplot(111)
        self.canvas_risk = FigureCanvasTkAgg(self.fig_risk, master=self.tab_charts)
        self.canvas_risk.get_tk_widget().grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

    def _build_tables_tab(self):
        """Constructs tables for best and least selling products."""
        self.tab_tables.columnconfigure(0, weight=1)
        self.tab_tables.columnconfigure(1, weight=1)
        self.tab_tables.rowconfigure(0, weight=1)

        # Best Selling Frame
        best_frame = tk.LabelFrame(
            self.tab_tables,
            text=" 🏆 Best-Selling Products (High Demand) ",
            font=FONTS["h3"],
            bg=THEME["white"],
            fg=THEME["text_primary"],
            padx=8,
            pady=8
        )
        best_frame.grid(row=0, column=0, sticky="nsew", padx=(5, 5), pady=5)
        best_frame.columnconfigure(0, weight=1)
        best_frame.rowconfigure(0, weight=1)

        cols = ("id", "name", "category", "sold", "revenue", "profit")
        self.tree_best = ttk.Treeview(best_frame, columns=cols, show="headings", height=12)
        self.tree_best.heading("id", text="ID")
        self.tree_best.heading("name", text="Product Name")
        self.tree_best.heading("category", text="Category")
        self.tree_best.heading("sold", text="Units")
        self.tree_best.heading("revenue", text="Revenue")
        self.tree_best.heading("profit", text="Gross Profit")

        self.tree_best.column("id", width=70, anchor="center")
        self.tree_best.column("name", width=180, anchor="w")
        self.tree_best.column("category", width=100, anchor="w")
        self.tree_best.column("sold", width=55, anchor="center")
        self.tree_best.column("revenue", width=75, anchor="e")
        self.tree_best.column("profit", width=75, anchor="e")

        sb_best = ttk.Scrollbar(best_frame, orient="vertical", command=self.tree_best.yview)
        self.tree_best.configure(yscrollcommand=sb_best.set)
        self.tree_best.grid(row=0, column=0, sticky="nsew")
        sb_best.grid(row=0, column=1, sticky="ns")

        # Least Selling Frame
        least_frame = tk.LabelFrame(
            self.tab_tables,
            text=" ⚠️ Slow-Moving / Dead Stock Risk ",
            font=FONTS["h3"],
            bg=THEME["white"],
            fg=THEME["text_primary"],
            padx=8,
            pady=8
        )
        least_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 5), pady=5)
        least_frame.columnconfigure(0, weight=1)
        least_frame.rowconfigure(0, weight=1)

        self.tree_least = ttk.Treeview(least_frame, columns=cols, show="headings", height=12)
        self.tree_least.heading("id", text="ID")
        self.tree_least.heading("name", text="Product Name")
        self.tree_least.heading("category", text="Category")
        self.tree_least.heading("sold", text="Units")
        self.tree_least.heading("revenue", text="Revenue")
        self.tree_least.heading("profit", text="Gross Profit")

        self.tree_least.column("id", width=70, anchor="center")
        self.tree_least.column("name", width=180, anchor="w")
        self.tree_least.column("category", width=100, anchor="w")
        self.tree_least.column("sold", width=55, anchor="center")
        self.tree_least.column("revenue", width=75, anchor="e")
        self.tree_least.column("profit", width=75, anchor="e")

        sb_least = ttk.Scrollbar(least_frame, orient="vertical", command=self.tree_least.yview)
        self.tree_least.configure(yscrollcommand=sb_least.set)
        self.tree_least.grid(row=0, column=0, sticky="nsew")
        sb_least.grid(row=0, column=1, sticky="ns")

    def _render_kpis(self, kpi: dict):
        """Renders 6 top KPI summary cards."""
        for widget in self.kpi_container.winfo_children():
            widget.destroy()

        cards = [
            ("Total Gross Revenue", format_currency(kpi["total_revenue"]), f"{kpi['total_transactions']} Transactions", THEME["navy_accent"]),
            ("Estimated Profit", format_currency(kpi["potential_profit"]), "Retail - Cost Value", THEME["success"]),
            ("Avg Order Value", format_currency(kpi["avg_order_value"]), "Revenue / Transaction", THEME["info"]),
            ("Inventory Cost Valuation", format_currency(kpi["total_inventory_cost"]), f"{format_quantity(kpi['total_stock_units'])} Units in Stock", THEME["text_secondary"]),
            ("Low Stock Alerts", f"{kpi['low_stock_count']} Items", "Below Minimum Stock", THEME["warning"]),
            ("Expiry Alerts (30d)", f"{kpi['expiring_soon_count'] + kpi['expired_count']} Items", f"{kpi['expired_count']} already expired", THEME["danger"]),
        ]

        for idx, (title, val, sub, color) in enumerate(cards):
            card = tk.Frame(self.kpi_container, bg=THEME["white"], bd=1, relief="solid", padx=10, pady=8)
            card.grid(row=0, column=idx, padx=4, pady=2, sticky="ew")

            tk.Label(card, text=title, font=FONTS["card_title"], bg=THEME["white"], fg=THEME["text_muted"]).pack(anchor="w")
            tk.Label(card, text=val, font=FONTS["card_value"], bg=THEME["white"], fg=color).pack(anchor="w", pady=(2, 2))
            tk.Label(card, text=sub, font=FONTS["card_sub"], bg=THEME["white"], fg=THEME["text_muted"]).pack(anchor="w")

    def refresh_data(self):
        """Recalculates all analytics and updates charts and tables."""
        kpi = compute_kpis(self.storage)
        self._render_kpis(kpi)

        # 1. Update Chart 1: Sales Trend
        days = self.selected_window.get()
        trend_df = get_sales_trend_data(self.storage, days_window=days)
        self.ax_sales.clear()
        self.ax_sales.set_facecolor("#FAFAFA")
        self.fig_sales.set_facecolor(THEME["white"])

        if not trend_df.empty:
            dates = trend_df["sale_date"]
            revs = trend_df["revenue"]
            self.ax_sales.plot(dates, revs, marker="o", markersize=3, color=THEME["navy_accent"], linewidth=2)
            self.ax_sales.set_title(f"Sales Revenue Trend (Past {days if days > 0 else 'All'} Days)", fontsize=9, fontweight="bold", color=THEME["navy_dark"])
            # Format x labels
            tick_step = max(1, len(dates) // 6)
            self.ax_sales.set_xticks(range(0, len(dates), tick_step))
            self.ax_sales.set_xticklabels([dates.iloc[i] for i in range(0, len(dates), tick_step)], rotation=20, ha="right", fontsize=7)
            self.ax_sales.tick_params(axis="y", labelsize=7)
            self.ax_sales.set_ylabel("Revenue (₹)", fontsize=8)
            self.ax_sales.grid(True, linestyle="--", alpha=0.5)
        else:
            self.ax_sales.text(0.5, 0.5, "No sales recorded in this period", ha="center", va="center", color=THEME["text_muted"])

        self.fig_sales.tight_layout()
        self.canvas_sales.draw()

        # 2. Update Chart 2: Category Distribution
        cat_df = get_category_analytics(self.storage)
        self.ax_cat.clear()
        self.ax_cat.set_facecolor("#FAFAFA")
        self.fig_cat.set_facecolor(THEME["white"])

        if not cat_df.empty:
            cats = cat_df["category"].tolist()[:6]
            stock_u = cat_df["stock_units"].tolist()[:6]
            colors = ["#1E3A8A", "#2563EB", "#0284C7", "#0D9488", "#10B981", "#F59E0B"][:len(cats)]
            bars = self.ax_cat.bar(cats, stock_u, color=colors, width=0.6)
            self.ax_cat.set_title("Stock Units by Category (Top 6)", fontsize=9, fontweight="bold", color=THEME["navy_dark"])
            self.ax_cat.set_xticks(range(len(cats)))
            self.ax_cat.set_xticklabels(cats, rotation=25, ha="right", fontsize=7)
            self.ax_cat.tick_params(axis="y", labelsize=7)
            self.ax_cat.grid(axis="y", linestyle="--", alpha=0.5)
            # Label bars
            for bar in bars:
                h = bar.get_height()
                self.ax_cat.annotate(f"{int(h)}", xy=(bar.get_x() + bar.get_width() / 2, h),
                                    xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=7)
        self.fig_cat.tight_layout()
        self.canvas_cat.draw()

        # 3. Update Chart 3: Top Selling
        best_df, least_df = get_product_sales_ranking(self.storage)
        self.ax_top.clear()
        self.ax_top.set_facecolor("#FAFAFA")
        self.fig_top.set_facecolor(THEME["white"])

        if not best_df.empty and best_df["units_sold"].sum() > 0:
            top5 = best_df.head(5).iloc[::-1]  # reverse so highest is on top
            short_names = [f"{row['product_name'][:18]}.." if len(row['product_name']) > 18 else row['product_name'] for _, row in top5.iterrows()]
            self.ax_top.barh(short_names, top5["units_sold"], color="#2563EB", height=0.55)
            self.ax_top.set_title("Top 5 Products by Units Sold", fontsize=9, fontweight="bold", color=THEME["navy_dark"])
            self.ax_top.tick_params(axis="both", labelsize=7)
            self.ax_top.grid(axis="x", linestyle="--", alpha=0.5)
        else:
            self.ax_top.text(0.5, 0.5, "No sales transactions to rank", ha="center", va="center", color=THEME["text_muted"])

        self.fig_top.tight_layout()
        self.canvas_top.draw()

        # 4. Update Chart 4: Inventory Health & Stock Status
        self.ax_risk.clear()
        self.fig_risk.set_facecolor(THEME["white"])

        safe_count = max(0, kpi["total_products"] - kpi["low_stock_count"] - kpi["expired_count"])
        labels = []
        sizes = []
        colors = []

        if safe_count > 0:
            labels.append("Safe")
            sizes.append(safe_count)
            colors.append("#10B981")
        if kpi["low_stock_count"] > 0:
            labels.append("Low Stock")
            sizes.append(kpi["low_stock_count"])
            colors.append("#F59E0B")
        if kpi["expired_count"] > 0:
            labels.append("Expired")
            sizes.append(kpi["expired_count"])
            colors.append("#EF4444")

        if sizes:
            self.ax_risk.pie(
                sizes,
                labels=labels,
                autopct="%1.0f%%",
                startangle=140,
                colors=colors,
                textprops={"fontsize": 7, "color": THEME["text_primary"]}
            )
            self.ax_risk.set_title("Inventory Health Status", fontsize=9, fontweight="bold", color=THEME["navy_dark"])
        else:
            self.ax_risk.text(0.5, 0.5, "No product inventory loaded", ha="center", va="center", color=THEME["text_muted"])

        self.fig_risk.tight_layout()
        self.canvas_risk.draw()

        # Update Tables
        self._populate_table(self.tree_best, best_df.head(15))
        self._populate_table(self.tree_least, least_df.head(15))

    def _populate_table(self, tree: ttk.Treeview, df: pd.DataFrame):
        for item in tree.get_children():
            tree.delete(item)
        if df.empty:
            return
        for _, row in df.iterrows():
            tree.insert("", "end", values=(
                row["product_id"],
                row["product_name"],
                row["category"],
                int(row["units_sold"]),
                format_currency(row["revenue"]),
                format_currency(row["gross_profit"]),
            ))

    def _export_analytics_report(self):
        """Exports analytics data to a user-selected CSV."""
        best_df, least_df = get_product_sales_ranking(self.storage)
        if best_df.empty:
            messagebox.showinfo("Export", "No analytics data available to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"store_analytics_report_{date.today().strftime('%Y%m%d')}.csv"
        )
        if not file_path:
            return

        try:
            best_df.to_csv(file_path, index=False)
            messagebox.showinfo("Export Successful", f"Analytics report saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not write CSV: {e}")
