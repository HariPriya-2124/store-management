"""
Dashboard Overview Module for Store Management System.
Displays key business KPI summary cards, embedded Matplotlib analytics charts,
and operational alert banners.
"""

from datetime import date
import tkinter as tk
from tkinter import ttk
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
from modules.analytics import (
    compute_kpis,
    get_category_analytics,
    get_product_sales_ranking,
    get_sales_trend_data,
)
from utils.helpers import format_currency, format_quantity
from utils.logger import get_logger

logger = get_logger("Dashboard")


class DashboardView(ttk.Frame):
    """
    Main Executive Dashboard View presenting high-level store health,
    revenue trends, inventory balances, and critical warnings.
    """

    def __init__(self, parent: tk.Widget, storage: StorageManager, nav_callback=None):
        super().__init__(parent)
        self.storage = storage
        self.nav_callback = nav_callback

        self._build_ui()
        self.refresh_dashboard()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # 1. Title & Action Bar
        top_bar = tk.Frame(self, bg=THEME["gray_bg"])
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 8))

        welcome_lbl = tk.Label(
            top_bar,
            text="Store Management Dashboard",
            font=FONTS["h1"],
            bg=THEME["gray_bg"],
            fg=THEME["text_primary"],
        )
        welcome_lbl.pack(side="left")

        actions_frame = tk.Frame(top_bar, bg=THEME["gray_bg"])
        actions_frame.pack(side="right")

        refresh_btn = tk.Button(
            actions_frame,
            text="🔄 Refresh Dashboard",
            command=self.refresh_dashboard,
            bg=THEME["navy_accent"],
            fg=THEME["white"],
            font=FONTS["caption_bold"],
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
        )
        refresh_btn.pack(side="left", padx=5)

        # 2. KPI Summary Cards Grid (6 cards)
        self.cards_frame = tk.Frame(self, bg=THEME["gray_bg"])
        self.cards_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        for i in range(6):
            self.cards_frame.columnconfigure(i, weight=1)

        # 3. Main Body: Split between Operational Alerts & 2x2 Charts
        content_frame = tk.Frame(self, bg=THEME["gray_bg"])
        content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 15))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)

        # Operational Warning Banner
        self.alert_banner = tk.Frame(content_frame, bg=THEME["white"], bd=1, relief="solid", padx=12, pady=6)
        self.alert_banner.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.alert_lbl = tk.Label(
            self.alert_banner,
            text="",
            font=FONTS["body_bold"],
            bg=THEME["white"],
            fg=THEME["warning"]
        )
        self.alert_lbl.pack(side="left")

        self.alert_action_btn = tk.Button(
            self.alert_banner,
            text="View Expiry Alerts →",
            command=lambda: self._navigate_to("expiry_alerts"),
            bg=THEME["danger"],
            fg=THEME["white"],
            font=FONTS["caption_bold"],
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2"
        )
        self.alert_action_btn.pack(side="right")

        # Visual Charts Grid 2x2
        charts_container = tk.Frame(content_frame, bg=THEME["gray_bg"])
        charts_container.grid(row=1, column=0, sticky="nsew")
        charts_container.columnconfigure(0, weight=1)
        charts_container.columnconfigure(1, weight=1)
        charts_container.rowconfigure(0, weight=1)
        charts_container.rowconfigure(1, weight=1)

        # Chart 1: Sales Trend
        self.fig_sales = Figure(figsize=(5.2, 2.5), dpi=100)
        self.ax_sales = self.fig_sales.add_subplot(111)
        self.canvas_sales = FigureCanvasTkAgg(self.fig_sales, master=charts_container)
        self.canvas_sales.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Chart 2: Category Inventory
        self.fig_cat = Figure(figsize=(5.2, 2.5), dpi=100)
        self.ax_cat = self.fig_cat.add_subplot(111)
        self.canvas_cat = FigureCanvasTkAgg(self.fig_cat, master=charts_container)
        self.canvas_cat.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Chart 3: Top Selling
        self.fig_top = Figure(figsize=(5.2, 2.5), dpi=100)
        self.ax_top = self.fig_top.add_subplot(111)
        self.canvas_top = FigureCanvasTkAgg(self.fig_top, master=charts_container)
        self.canvas_top.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Chart 4: Stock Status
        self.fig_status = Figure(figsize=(5.2, 2.5), dpi=100)
        self.ax_status = self.fig_status.add_subplot(111)
        self.canvas_status = FigureCanvasTkAgg(self.fig_status, master=charts_container)
        self.canvas_status.get_tk_widget().grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

    def _navigate_to(self, target: str):
        if self.nav_callback:
            self.nav_callback(target)

    def refresh_dashboard(self):
        """Fetches fresh data from storage and updates all dashboard components."""
        kpis = compute_kpis(self.storage)

        # 1. Update KPI Cards
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        cards_data = [
            ("Total Products", format_quantity(kpis["total_products"]), "Registered items", THEME["navy_accent"]),
            ("Total Suppliers", format_quantity(kpis["total_suppliers"]), "Active partners", THEME["info"]),
            ("Total Stock Units", format_quantity(kpis["total_stock_units"]), f"Cost: {format_currency(kpis['total_inventory_cost'])}", THEME["text_secondary"]),
            ("Total Sales Revenue", format_currency(kpis["total_revenue"]), f"{kpis['total_transactions']} sales transactions", THEME["success"]),
            ("Low-Stock Items", f"{kpis['low_stock_count']}", "At or below reorder level", THEME["warning"]),
            ("Near-Expiry (30d)", f"{kpis['expiring_soon_count'] + kpis['expired_count']}", f"{kpis['expired_count']} expired items", THEME["danger"]),
        ]

        for i, (title, val, sub, color) in enumerate(cards_data):
            card = tk.Frame(self.cards_frame, bg=THEME["white"], bd=1, relief="solid", padx=10, pady=8)
            card.grid(row=0, column=i, padx=4, pady=2, sticky="ew")

            tk.Label(card, text=title, font=FONTS["card_title"], bg=THEME["white"], fg=THEME["text_muted"]).pack(anchor="w")
            tk.Label(card, text=val, font=FONTS["card_value"], bg=THEME["white"], fg=color).pack(anchor="w", pady=(2, 2))
            tk.Label(card, text=sub, font=FONTS["card_sub"], bg=THEME["white"], fg=THEME["text_muted"]).pack(anchor="w")

        # 2. Update Alert Banner
        if kpis["expired_count"] > 0 or kpis["low_stock_count"] > 0:
            alert_text = (
                f"⚠️ Attention Required: {kpis['expired_count']} item(s) have EXPIRED, "
                f"{kpis['expiring_soon_count']} expiring within 7 days, "
                f"and {kpis['low_stock_count']} item(s) are low on stock."
            )
            self.alert_lbl.config(text=alert_text, fg=THEME["danger"])
            self.alert_banner.config(bg=THEME["danger_bg"])
            self.alert_lbl.config(bg=THEME["danger_bg"])
        else:
            self.alert_lbl.config(text="✓ All product inventory is well-stocked and within safe shelf life.", fg=THEME["success"])
            self.alert_banner.config(bg=THEME["success_bg"])
            self.alert_lbl.config(bg=THEME["success_bg"])

        # 3. Update Chart 1: Sales Trend
        trend_df = get_sales_trend_data(self.storage, days_window=30)
        self.ax_sales.clear()
        self.ax_sales.set_facecolor("#FAFAFA")
        self.fig_sales.set_facecolor(THEME["white"])

        if not trend_df.empty:
            dates = trend_df["sale_date"]
            revs = trend_df["revenue"]
            self.ax_sales.plot(dates, revs, marker="o", markersize=3, color=THEME["navy_accent"], linewidth=2)
            self.ax_sales.set_title("30-Day Sales Revenue Trend", fontsize=9, fontweight="bold", color=THEME["navy_dark"])
            step = max(1, len(dates) // 5)
            self.ax_sales.set_xticks(range(0, len(dates), step))
            self.ax_sales.set_xticklabels([dates.iloc[i] for i in range(0, len(dates), step)], rotation=20, ha="right", fontsize=7)
            self.ax_sales.tick_params(axis="y", labelsize=7)
            self.ax_sales.set_ylabel("Revenue (₹)", fontsize=7)
            self.ax_sales.grid(True, linestyle="--", alpha=0.5)
        else:
            self.ax_sales.text(0.5, 0.5, "No sales recorded yet", ha="center", va="center", color=THEME["text_muted"])

        self.fig_sales.tight_layout()
        self.canvas_sales.draw()

        # 4. Update Chart 2: Category Inventory
        cat_df = get_category_analytics(self.storage)
        self.ax_cat.clear()
        self.ax_cat.set_facecolor("#FAFAFA")
        self.fig_cat.set_facecolor(THEME["white"])

        if not cat_df.empty:
            top_cats = cat_df.head(5)
            cats = [c[:12] + ".." if len(c) > 12 else c for c in top_cats["category"]]
            units = top_cats["stock_units"]
            bars = self.ax_cat.bar(cats, units, color="#1E3A8A", width=0.55)
            self.ax_cat.set_title("Stock Units by Top Categories", fontsize=9, fontweight="bold", color=THEME["navy_dark"])
            self.ax_cat.tick_params(axis="both", labelsize=7)
            self.ax_cat.set_xticks(range(len(cats)))
            self.ax_cat.set_xticklabels(cats, rotation=20, ha="right", fontsize=7)
            self.ax_cat.grid(axis="y", linestyle="--", alpha=0.5)
            for bar in bars:
                h = bar.get_height()
                self.ax_cat.annotate(f"{int(h)}", xy=(bar.get_x() + bar.get_width() / 2, h),
                                     xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=7)
        self.fig_cat.tight_layout()
        self.canvas_cat.draw()

        # 5. Update Chart 3: Top Selling
        best_df, _ = get_product_sales_ranking(self.storage)
        self.ax_top.clear()
        self.ax_top.set_facecolor("#FAFAFA")
        self.fig_top.set_facecolor(THEME["white"])

        if not best_df.empty and best_df["units_sold"].sum() > 0:
            top5 = best_df.head(5).iloc[::-1]
            names = [r["product_name"][:16] + ".." if len(r["product_name"]) > 16 else r["product_name"] for _, r in top5.iterrows()]
            self.ax_top.barh(names, top5["units_sold"], color="#2563EB", height=0.55)
            self.ax_top.set_title("Top 5 Fast-Moving Products (Units Sold)", fontsize=9, fontweight="bold", color=THEME["navy_dark"])
            self.ax_top.tick_params(axis="both", labelsize=7)
            self.ax_top.grid(axis="x", linestyle="--", alpha=0.5)
        else:
            self.ax_top.text(0.5, 0.5, "No sales recorded yet", ha="center", va="center", color=THEME["text_muted"])

        self.fig_top.tight_layout()
        self.canvas_top.draw()

        # 6. Update Chart 4: Stock Status Pie
        self.ax_status.clear()
        self.fig_status.set_facecolor(THEME["white"])

        safe_cnt = max(0, kpis["total_products"] - kpis["low_stock_count"] - kpis["expired_count"])
        labels = []
        sizes = []
        colors = []

        if safe_cnt > 0:
            labels.append("Adequate")
            sizes.append(safe_cnt)
            colors.append("#10B981")
        if kpis["low_stock_count"] > 0:
            labels.append("Low Stock")
            sizes.append(kpis["low_stock_count"])
            colors.append("#F59E0B")
        if kpis["expired_count"] > 0:
            labels.append("Expired")
            sizes.append(kpis["expired_count"])
            colors.append("#EF4444")

        if sizes:
            self.ax_status.pie(
                sizes,
                labels=labels,
                autopct="%1.0f%%",
                startangle=140,
                colors=colors,
                textprops={"fontsize": 7, "color": THEME["text_primary"]}
            )
            self.ax_status.set_title("Inventory Stock Health Ratio", fontsize=9, fontweight="bold", color=THEME["navy_dark"])
        else:
            self.ax_status.text(0.5, 0.5, "No inventory loaded", ha="center", va="center", color=THEME["text_muted"])

        self.fig_status.tight_layout()
        self.canvas_status.draw()
