"""
Inventory Management Module for Store Management System.
Faithfully reproduces the reference FactoryFlow Inventory Dashboard:
- Presentation Canvas Frame (#0A0D10) with 'PAGE 2' green pill badge,
  'CRUD Operations Dashboard' title, and 'Central navigation hub' subtitle.
- FactoryFlow Dark Dashboard System (#10141D):
  • Left Sidebar: Logo, Navigation hierarchy, Active 'Inventory Dashboard' pill,
    nested sub-items (Brands, Categories, Groups, Items, UOM, Expenses),
    and bottom 'factoryflow.app' tag.
  • Top Navigation Bar: Search bar, theme toggle (☼), chat, tasks, notifications (🔔),
    and user profile avatar ('Aadel' / active user).
  • 4 Stat Cards: Total Items (2,456), Item Brands (89), Categories (156), Suppliers (234).
  • Quick Actions: Add Brand, Add Category, Add Group, Add Item, Add UOM, Add Expense,
    Add Supplier, Add Location, plus Stock-In, Stock-Out, Physical Audit, and Export CSV.
  • Analytical Charts:
    - 'Inventory Trends' line chart with monthly data, grid lines, and interactive tooltip.
    - 'Stock Status' donut chart with 'In Stock: 35 (39%)' and color-coded status distribution.
  • Interactive Live Items Table & Movements Audit Ledger with status filtering and search.
"""

from datetime import date, datetime
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
from PIL import Image, ImageTk

# Base directory setup
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from config import ASSETS_DIR, DATA_DIR, FONTS, THEME
except Exception:
    ASSETS_DIR = BASE_DIR / "assets"
    DATA_DIR = BASE_DIR / "data"
    FONTS = {}
    THEME = {}

from database.storage_manager import StorageManager
from utils.helpers import (
    export_dataframe_to_csv,
    format_currency,
    format_quantity,
    safe_float,
    safe_int
)
from utils.logger import get_logger
from utils.validators import validate_integer

logger = get_logger("InventoryModule")

# =============================================================================
# THEME COLOR CONSTANTS
# =============================================================================

BG_CANVAS = "#0A0D10"
BG_APP = "#10141D"
BG_SIDEBAR = "#141A26"
BG_HEADER = "#141A26"
BG_CARD = "#161D2C"
BG_CARD_ALT = "#192233"
BORDER_DARK = "#202A3C"
BORDER_HIGHLIGHT = "#2E3A52"

TEXT_WHITE = "#FFFFFF"
TEXT_MUTED = "#8A94A6"
TEXT_MUTED_LIGHT = "#A0ABC0"

ACCENT_PURPLE = "#7C3AED"
ACCENT_PURPLE_LIGHT = "#8B5CF6"
ACCENT_BLUE = "#2563EB"
ACCENT_BLUE_LIGHT = "#38BDF8"
ACCENT_GREEN = "#10B981"
ACCENT_ORANGE = "#F59E0B"
ACCENT_RED = "#EF4444"
ACCENT_TEAL = "#14B8A6"
ACCENT_GRAY = "#64748B"


# =============================================================================
# INVENTORY MANAGEMENT VIEW (FACTORYFLOW DASHBOARD)
# =============================================================================

class InventoryManagementView(tk.Frame):
    """
    FactoryFlow Inventory Dashboard matching the reference design:
    - 4 KPI Stat Cards
    - 8 Quick Actions (Brand, Category, Group, Item, UOM, Expense, Supplier, Location)
    - 2 Live Analytical Charts (Inventory Trends Line Chart & Stock Status Donut Chart)
    - Interactive Stock Management Data Table and Movement Ledger
    """

    def __init__(
        self,
        parent: tk.Widget,
        storage: Optional[StorageManager] = None,
        on_inventory_changed=None,
        nav_callback=None,
        show_presentation_frame: bool = False
    ):
        super().__init__(parent, bg=BG_APP)

        self.storage = storage or StorageManager(auto_init=True)
        self.on_inventory_changed = on_inventory_changed
        self.nav_callback = nav_callback
        self.show_presentation_frame = show_presentation_frame

        self.df_products = pd.DataFrame()
        self.df_movements = pd.DataFrame()
        self._icon_cache = {}

        self._load_badge_icons()
        self._build_ui()
        self.load_data()

    # =========================================================================
    # ICON ASSETS
    # =========================================================================

    def _load_badge_icons(self):
        """Loads and caches icon badges for cards and quick actions."""
        icons_dir = ASSETS_DIR / "icons"
        icons_dir.mkdir(parents=True, exist_ok=True)

        icon_files = {
            "logo": ("factoryflow_logo.png", (34, 34)),
            "items": ("badge_items.png", (44, 44)),
            "brands": ("badge_brands.png", (44, 44)),
            "categories": ("badge_categories.png", (44, 44)),
            "suppliers": ("badge_suppliers.png", (44, 44)),
            "act_brand": ("action_brand.png", (36, 36)),
            "act_cat": ("action_category.png", (36, 36)),
            "act_group": ("action_group.png", (36, 36)),
            "act_item": ("action_item.png", (36, 36)),
            "act_uom": ("action_uom.png", (36, 36)),
            "act_expense": ("action_expense.png", (36, 36)),
            "act_supplier": ("action_supplier.png", (36, 36)),
            "act_loc": ("action_location.png", (36, 36)),
        }

        for key, (fname, size) in icon_files.items():
            fpath = icons_dir / fname
            if fpath.exists():
                try:
                    img = Image.open(fpath).resize(size, Image.Resampling.LANCZOS)
                    self._icon_cache[key] = ImageTk.PhotoImage(img)
                except Exception as e:
                    logger.warning(f"Error loading icon {key}: {e}")

    # =========================================================================
    # UI CONSTRUCTION
    # =========================================================================

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Main Layout Container
        self.app_container = tk.Frame(self, bg=BG_APP)
        self.app_container.grid(row=0, column=0, sticky="nsew")
        self.app_container.columnconfigure(1, weight=1)
        self.app_container.rowconfigure(0, weight=1)

        # 1. Left Sidebar
        self._build_sidebar(self.app_container)

        # 2. Main Content Container
        self.main_content = tk.Frame(self.app_container, bg=BG_APP)
        self.main_content.grid(row=0, column=1, sticky="nsew")
        self.main_content.columnconfigure(0, weight=1)
        self.main_content.rowconfigure(1, weight=1)

        # 2a. Top Navigation Bar
        self._build_top_navbar(self.main_content)

        # 2b. Scrollable Dashboard Area
        self._build_dashboard_body(self.main_content)

    # =========================================================================
    # LEFT SIDEBAR
    # =========================================================================

    def _build_sidebar(self, parent):
        """Builds the FactoryFlow sidebar navigation hierarchy."""
        sidebar = tk.Frame(parent, bg=BG_SIDEBAR, width=220, highlightthickness=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # 1. Brand Logo Header
        brand_frame = tk.Frame(sidebar, bg=BG_SIDEBAR, padx=14, pady=16)
        brand_frame.pack(fill="x")

        if "logo" in self._icon_cache:
            lbl_logo = tk.Label(brand_frame, image=self._icon_cache["logo"], bg=BG_SIDEBAR)
            lbl_logo.pack(side="left", padx=(0, 10))

        brand_text_box = tk.Frame(brand_frame, bg=BG_SIDEBAR)
        brand_text_box.pack(side="left")

        tk.Label(
            brand_text_box,
            text="FactoryFlow",
            font=("Arial", 13, "bold"),
            fg=TEXT_WHITE,
            bg=BG_SIDEBAR
        ).pack(anchor="w")

        tk.Label(
            brand_text_box,
            text="Management System",
            font=("Arial", 9),
            fg=TEXT_MUTED,
            bg=BG_SIDEBAR
        ).pack(anchor="w")

        btn_collapse = tk.Label(
            brand_frame,
            text="‹",
            font=("Arial", 13, "bold"),
            fg=TEXT_MUTED,
            bg=BG_SIDEBAR,
            cursor="hand2"
        )
        btn_collapse.pack(side="right")

        # Separator line
        tk.Frame(sidebar, bg=BORDER_DARK, height=1).pack(fill="x", padx=14, pady=(0, 10))

        # 2. Sidebar Navigation Items
        nav_canvas = tk.Canvas(sidebar, bg=BG_SIDEBAR, highlightthickness=0)
        nav_canvas.pack(fill="both", expand=True)

        nav_frame = tk.Frame(nav_canvas, bg=BG_SIDEBAR)
        nav_canvas.create_window((0, 0), window=nav_frame, anchor="nw", width=220)

        menu_items = [
            ("📊", "Dashboard", False, None),
            ("👥", "CRMS", False, "⌵"),
            ("⚙", "Design Rework", False, "⌵"),
            ("🔘", "Cylinder Rework", False, "⌵"),
            ("📋", "Work Order", False, "⌵"),
            ("📦", "Production", False, "⌵"),
            ("📅", "Jobs", False, "⌵"),
        ]

        for icon, title, is_active, arrow in menu_items:
            self._create_sidebar_item(nav_frame, icon, title, is_active, arrow)

        # 3. Active / Expanded Menu: INVENTORY
        inv_header = tk.Frame(nav_frame, bg=BG_SIDEBAR, padx=14, pady=5)
        inv_header.pack(fill="x")

        tk.Label(inv_header, text="📦", font=("Arial", 11), fg=ACCENT_PURPLE_LIGHT, bg=BG_SIDEBAR).pack(side="left", padx=(0, 8))
        tk.Label(inv_header, text="Inventory", font=("Arial", 11, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(side="left")
        tk.Label(inv_header, text="˄", font=("Arial", 11), fg=ACCENT_PURPLE_LIGHT, bg=BG_SIDEBAR).pack(side="right")

        # Nested Sub-menu
        sub_items = [
            ("🗂", "Inventory Dashboard", True, lambda: self._switch_tab("dashboard")),
            ("🏷", "Item Brand", False, lambda: self._show_info_modal("Item Brand", "Brand catalog management.")),
            ("📁", "Item Category", False, lambda: self._show_info_modal("Item Category", "Manage 156 product categories.")),
            ("📦", "Item Group", False, lambda: self._show_info_modal("Item Group", "Organize items into inventory groups.")),
            ("📄", "Items", False, lambda: self._switch_tab("table")),
            ("📐", "UOM", False, lambda: self._show_info_modal("UOM", "Unit of Measure configurations.")),
            ("💰", "Expense Types", False, lambda: self._show_info_modal("Expense Types", "Track inventory-related operational expenses.")),
        ]

        for icon, sub_title, is_sub_active, cmd in sub_items:
            row_bg = ACCENT_PURPLE if is_sub_active else BG_SIDEBAR
            txt_color = TEXT_WHITE if is_sub_active else TEXT_MUTED_LIGHT
            f = tk.Frame(nav_frame, bg=row_bg, padx=14, pady=5)
            f.pack(fill="x", padx=10, pady=1)

            lbl_sub = tk.Label(
                f,
                text=f"  {icon}  {sub_title}",
                font=("Arial", 10, "bold" if is_sub_active else "normal"),
                fg=txt_color,
                bg=row_bg,
                cursor="hand2"
            )
            lbl_sub.pack(anchor="w")
            if cmd:
                lbl_sub.bind("<Button-1>", lambda e, c=cmd: c())

        # 4. Bottom Tag: 'factoryflow.app'
        bottom_box = tk.Frame(sidebar, bg=BG_SIDEBAR, padx=14, pady=12)
        bottom_box.pack(side="bottom", fill="x")

        tk.Label(
            bottom_box,
            text="factoryflow.app",
            font=("Arial", 10, "bold"),
            fg=TEXT_MUTED,
            bg="#1E2838",
            padx=12,
            pady=4
        ).pack(anchor="w")

        tk.Label(
            bottom_box,
            text="11 modules  •  FactoryFlow v1.0",
            font=("Arial", 8),
            fg="#5A667A",
            bg=BG_SIDEBAR
        ).pack(anchor="w", pady=(6, 0))

    def _create_sidebar_item(self, parent, icon, title, is_active, arrow=None):
        """Creates a standard clickable sidebar navigation row."""
        f = tk.Frame(parent, bg=BG_SIDEBAR, padx=14, pady=6)
        f.pack(fill="x")

        tk.Label(f, text=icon, font=("Arial", 11), fg=TEXT_MUTED, bg=BG_SIDEBAR).pack(side="left", padx=(0, 8))
        tk.Label(f, text=title, font=("Arial", 10), fg=TEXT_MUTED_LIGHT, bg=BG_SIDEBAR).pack(side="left")

        if arrow:
            tk.Label(f, text=arrow, font=("Arial", 9), fg=TEXT_MUTED, bg=BG_SIDEBAR).pack(side="right")

    # =========================================================================
    # TOP NAVIGATION BAR
    # =========================================================================

    def _build_top_navbar(self, parent):
        """Top app bar with search and utilities."""
        navbar = tk.Frame(parent, bg=BG_HEADER, height=52, padx=20, pady=8)
        navbar.grid(row=0, column=0, sticky="ew")
        navbar.grid_propagate(False)

        # 1. Search Box
        search_frame = tk.Frame(navbar, bg="#192233", padx=8, pady=4, bd=1, relief="solid")
        search_frame.pack(side="left")

        tk.Label(search_frame, text="🔍", font=("Arial", 10), fg=TEXT_MUTED, bg="#192233").pack(side="left", padx=(0, 4))
        self.entry_search = tk.Entry(
            search_frame,
            font=("Arial", 10),
            fg=TEXT_WHITE,
            bg="#192233",
            bd=0,
            width=32,
            insertbackground=TEXT_WHITE
        )
        self.entry_search.pack(side="left")
        self.entry_search.insert(0, "Search...")
        self.entry_search.bind("<FocusIn>", lambda e: self._clear_search_placeholder())
        self.entry_search.bind("<KeyRelease>", lambda e: self.filter_monitor())

        # 2. Right utility controls
        right_box = tk.Frame(navbar, bg=BG_HEADER)
        right_box.pack(side="right")

        # Back to CRUD Hub button if nav_callback is provided
        if self.nav_callback:
            btn_hub = tk.Label(
                right_box,
                text="← CRUD Hub",
                font=("Arial", 10, "bold"),
                fg=TEXT_WHITE,
                bg=ACCENT_PURPLE,
                padx=10,
                pady=4,
                cursor="hand2"
            )
            btn_hub.pack(side="left", padx=(0, 14))
            btn_hub.bind("<Button-1>", lambda e: self.nav_callback("hub"))

        for icon_symbol in ["☼", "💬", "📋"]:
            btn = tk.Label(
                right_box,
                text=icon_symbol,
                font=("Arial", 12),
                fg=TEXT_MUTED,
                bg="#192233",
                width=3,
                cursor="hand2"
            )
            btn.pack(side="left", padx=4)

        # Bell Notification with alert dot
        btn_bell = tk.Label(
            right_box,
            text="🔔",
            font=("Arial", 12),
            fg=TEXT_MUTED,
            bg="#192233",
            width=3,
            cursor="hand2"
        )
        btn_bell.pack(side="left", padx=4)

        # User Avatar Profile
        user_box = tk.Frame(right_box, bg=BG_HEADER)
        user_box.pack(side="left", padx=(10, 0))

        tk.Label(user_box, text="👤", font=("Arial", 13), fg=TEXT_WHITE, bg="#2A3850", width=2).pack(side="left", padx=(0, 6))
        tk.Label(user_box, text="Aadel", font=("Arial", 11, "bold"), fg=TEXT_WHITE, bg=BG_HEADER).pack(side="left")

    def _clear_search_placeholder(self):
        if self.entry_search.get() == "Search...":
            self.entry_search.delete(0, "end")

    # =========================================================================
    # DASHBOARD BODY (STAT CARDS, QUICK ACTIONS, CHARTS, TABLE)
    # =========================================================================

    def _build_dashboard_body(self, parent):
        """Builds the main scrollable content area."""
        container = tk.Frame(parent, bg=BG_APP)
        container.grid(row=1, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        canvas = tk.Canvas(container, bg=BG_APP, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.body_frame = tk.Frame(canvas, bg=BG_APP, padx=22, pady=16)

        canvas.create_window((0, 0), window=self.body_frame, anchor="nw")
        canvas.configure(xscrollcommand=None, yscrollcommand=scrollbar.set)

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(1, width=event.width)

        canvas.bind("<Configure>", lambda e: canvas.itemconfig(1, width=e.width))
        self.body_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Mousewheel binding
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # 1. Header Title
        tk.Label(
            self.body_frame,
            text="Inventory Dashboard",
            font=("Arial", 20, "bold"),
            fg=TEXT_WHITE,
            bg=BG_APP
        ).pack(anchor="w", pady=(0, 2))

        tk.Label(
            self.body_frame,
            text="Inventory management system overview and insights.",
            font=("Arial", 11),
            fg=TEXT_MUTED,
            bg=BG_APP
        ).pack(anchor="w", pady=(0, 16))

        # 2. Section: 4 KPI Cards
        self._build_kpi_cards(self.body_frame)

        # 3. Section: Quick Actions
        self._build_quick_actions(self.body_frame)

        # 4. Section: Analytical Charts
        self._build_charts_section(self.body_frame)

        # 5. Section: Live Data Table & Audit Ledger
        self._build_table_section(self.body_frame)

    # =========================================================================
    # KPI STAT CARDS
    # =========================================================================

    def _build_kpi_cards(self, parent):
        """Constructs the 4 KPI stat cards."""
        card_row = tk.Frame(parent, bg=BG_APP)
        card_row.pack(fill="x", pady=(0, 18))

        for i in range(4):
            card_row.columnconfigure(i, weight=1, uniform="kpi")

        self.kpi_data = [
            ("Total Items", "2,456", "↑ 12% from last month", "items", 0),
            ("Item Brands", "89", "↑ 8% from last month", "brands", 1),
            ("Categories", "156", "↑ 15% from last month", "categories", 2),
            ("Suppliers", "234", "↑ 5% from last month", "suppliers", 3),
        ]

        self.kpi_value_labels = {}

        for title, val, trend, icon_key, col in self.kpi_data:
            card = tk.Frame(card_row, bg=BG_CARD, bd=1, relief="solid", highlightthickness=0)
            card.grid(row=0, column=col, sticky="nsew", padx=5)

            inner = tk.Frame(card, bg=BG_CARD, padx=16, pady=14)
            inner.pack(fill="both", expand=True)

            left_box = tk.Frame(inner, bg=BG_CARD)
            left_box.pack(side="left", fill="both", expand=True)

            tk.Label(
                left_box,
                text=title,
                font=("Arial", 10),
                fg=TEXT_MUTED,
                bg=BG_CARD
            ).pack(anchor="w")

            val_lbl = tk.Label(
                left_box,
                text=val,
                font=("Arial", 20, "bold"),
                fg=TEXT_WHITE,
                bg=BG_CARD
            )
            val_lbl.pack(anchor="w", pady=(2, 4))
            self.kpi_value_labels[title] = val_lbl

            tk.Label(
                left_box,
                text=trend,
                font=("Arial", 9),
                fg=ACCENT_GREEN,
                bg=BG_CARD
            ).pack(anchor="w")

            # Icon badge on right
            if icon_key in self._icon_cache:
                lbl_icon = tk.Label(inner, image=self._icon_cache[icon_key], bg=BG_CARD)
                lbl_icon.pack(side="right", padx=(8, 0))

    # =========================================================================
    # QUICK ACTIONS
    # =========================================================================

    def _build_quick_actions(self, parent):
        """Constructs the Quick Actions header and 8 horizontal action cards."""
        qa_frame = tk.Frame(parent, bg=BG_APP)
        qa_frame.pack(fill="x", pady=(0, 18))

        tk.Label(
            qa_frame,
            text="Quick Actions",
            font=("Arial", 14, "bold"),
            fg=TEXT_WHITE,
            bg=BG_APP
        ).pack(anchor="w")

        tk.Label(
            qa_frame,
            text="Common inventory management tasks",
            font=("Arial", 10),
            fg=TEXT_MUTED,
            bg=BG_APP
        ).pack(anchor="w", pady=(0, 10))

        btn_row = tk.Frame(qa_frame, bg=BG_APP)
        btn_row.pack(fill="x")

        actions = [
            ("Add Brand", "act_brand", lambda: self._show_info_modal("Add Brand", "Enter new brand name to register.")),
            ("Add Category", "act_cat", lambda: self._show_info_modal("Add Category", "Create new product category.")),
            ("Add Group", "act_group", lambda: self._show_info_modal("Add Group", "Create new item grouping.")),
            ("Add Item", "act_item", self._open_add_product_modal),
            ("Add UOM", "act_uom", lambda: self._show_info_modal("Add UOM", "Configure Unit of Measure.")),
            ("Add Expense", "act_expense", lambda: self._show_info_modal("Add Expense", "Record operational item expense.")),
            ("Add Supplier", "act_supplier", lambda: self._show_info_modal("Add Supplier", "Register new vendor/supplier.")),
            ("Add Location", "act_loc", lambda: self._show_info_modal("Add Location", "Define store warehouse shelf location.")),
        ]

        for i in range(len(actions)):
            btn_row.columnconfigure(i, weight=1, uniform="qa_btn")

        for idx, (title, icon_key, cmd) in enumerate(actions):
            card = tk.Frame(btn_row, bg=BG_CARD, bd=1, relief="solid", cursor="hand2")
            card.grid(row=0, column=idx, sticky="nsew", padx=4, pady=2)

            inner = tk.Frame(card, bg=BG_CARD, padx=6, pady=10)
            inner.pack(fill="both", expand=True)

            if icon_key in self._icon_cache:
                lbl_icon = tk.Label(inner, image=self._icon_cache[icon_key], bg=BG_CARD, cursor="hand2")
                lbl_icon.pack(pady=(0, 4))
                lbl_icon.bind("<Button-1>", lambda e, c=cmd: c())

            lbl_txt = tk.Label(
                inner,
                text=title,
                font=("Arial", 9, "bold"),
                fg=TEXT_WHITE,
                bg=BG_CARD,
                cursor="hand2"
            )
            lbl_txt.pack()

            card.bind("<Button-1>", lambda e, c=cmd: c())
            inner.bind("<Button-1>", lambda e, c=cmd: c())
            lbl_txt.bind("<Button-1>", lambda e, c=cmd: c())

    # =========================================================================
    # ANALYTICAL CHARTS (LINE & DONUT)
    # =========================================================================

    def _build_charts_section(self, parent):
        """Constructs the two-column charts: Inventory Trends & Stock Status."""
        charts_row = tk.Frame(parent, bg=BG_APP)
        charts_row.pack(fill="x", pady=(0, 18))

        charts_row.columnconfigure(0, weight=60, uniform="chart_col")
        charts_row.columnconfigure(1, weight=40, uniform="chart_col")

        # ── LEFT CARD: INVENTORY TRENDS ──────────────────────────────────────
        card_line = tk.Frame(charts_row, bg=BG_CARD, bd=1, relief="solid")
        card_line.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        header_line = tk.Frame(card_line, bg=BG_CARD, padx=16, pady=12)
        header_line.pack(fill="x")

        tk.Label(header_line, text="Inventory Trends", font=("Arial", 13, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        tk.Label(header_line, text="Monthly inventory trends", font=("Arial", 10), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")

        self.canvas_line = tk.Canvas(card_line, height=190, bg="#131926", highlightthickness=0)
        self.canvas_line.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self._draw_line_chart()

        # ── RIGHT CARD: STOCK STATUS ─────────────────────────────────────────
        card_donut = tk.Frame(charts_row, bg=BG_CARD, bd=1, relief="solid")
        card_donut.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        header_donut = tk.Frame(card_donut, bg=BG_CARD, padx=16, pady=12)
        header_donut.pack(fill="x")

        tk.Label(header_donut, text="Stock Status", font=("Arial", 13, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        tk.Label(header_donut, text="Current stock status distribution", font=("Arial", 10), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")

        self.canvas_donut = tk.Canvas(card_donut, height=190, bg="#131926", highlightthickness=0)
        self.canvas_donut.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self._draw_donut_chart()

    def _draw_line_chart(self):
        """Draws the glowing blue monthly trends chart with grid and tooltip."""
        c = self.canvas_line
        c.delete("all")

        # Horizontal Grid lines
        grid_data = [(35, "2800"), (80, "2100"), (125, "1400")]
        for y, val in grid_data:
            c.create_line(45, y, 460, y, fill="#1E2838", dash=(2, 4))
            c.create_text(25, y, text=val, fill=TEXT_MUTED, font=("Arial", 9))

        # Monthly line points
        pts = [(55, 95), (120, 92), (195, 96), (275, 88), (355, 84), (435, 78)]
        flat_pts = [coord for pt in pts for coord in pt]

        # Draw glowing path
        c.create_line(flat_pts, fill="#1E3A8A", width=5, smooth=True)
        c.create_line(flat_pts, fill=ACCENT_BLUE_LIGHT, width=2, smooth=True)

        for px, py in pts:
            c.create_oval(px - 4, py - 4, px + 4, py + 4, fill=ACCENT_BLUE_LIGHT, outline=TEXT_WHITE, width=2)

        # Interactive / Reference Tooltip Box at 'Feb' (120, 92)
        tx, ty = 120, 95
        c.create_rectangle(tx - 4, ty + 8, tx + 104, ty + 78, fill="#162032", outline="#2563EB", width=1)
        c.create_text(tx + 50, ty + 20, text="Feb", fill=TEXT_WHITE, font=("Arial", 9, "bold"))
        c.create_text(tx + 50, ty + 35, text="Categories : 158", fill=ACCENT_ORANGE, font=("Arial", 8))
        c.create_text(tx + 50, ty + 49, text="Items : 2523", fill=ACCENT_BLUE_LIGHT, font=("Arial", 8))
        c.create_text(tx + 50, ty + 63, text="Suppliers : 238", fill=ACCENT_TEAL, font=("Arial", 8))

    def _draw_donut_chart(self):
        """Draws the stock status donut chart with 'In Stock: 35 (39%)'."""
        c = self.canvas_donut
        c.delete("all")

        # Top stat text
        c.create_text(160, 20, text="In Stock: 35 (39%)", fill=ACCENT_GREEN, font=("Arial", 10, "bold"))

        # Donut dimensions
        cx, cy, r = 160, 110, 65
        r_inner = 34

        # Slices: In Stock (green), Low Stock (orange), Out of Stock (pink), Reorder (blue)
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=0, extent=140, fill=ACCENT_GREEN, outline="#131926", width=2)
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=140, extent=95, fill=ACCENT_ORANGE, outline="#131926", width=2)
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=235, extent=75, fill="#EC4899", outline="#131926", width=2)
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=310, extent=50, fill=ACCENT_BLUE, outline="#131926", width=2)

        # Inner hole
        c.create_oval(cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner, fill="#131926", outline="#131926")

        # Legend on the right side
        legends = [
            (ACCENT_GREEN, "Adequate"),
            (ACCENT_ORANGE, "Low Stock"),
            ("#EC4899", "Out of Stock"),
            (ACCENT_BLUE, "Reserved")
        ]
        for idx, (col, leg_txt) in enumerate(legends):
            ly = 60 + idx * 22
            c.create_rectangle(245, ly, 255, ly + 10, fill=col, outline="")
            c.create_text(262, ly + 5, text=leg_txt, fill=TEXT_MUTED, font=("Arial", 8), anchor="w")

    # =========================================================================
    # LIVE ITEMS TABLE & AUDIT LEDGER SECTION
    # =========================================================================

    def _build_table_section(self, parent):
        """Builds the interactive items table drawer with stock-in, stock-out, audit."""
        self.table_card = tk.Frame(parent, bg=BG_CARD, bd=1, relief="solid")
        self.table_card.pack(fill="x", pady=(0, 10))

        # Control Toolbar Header
        tb_header = tk.Frame(self.table_card, bg=BG_CARD, padx=16, pady=12)
        tb_header.pack(fill="x")

        # Title & Tabs
        title_box = tk.Frame(tb_header, bg=BG_CARD)
        title_box.pack(side="left")

        self.btn_tab_items = tk.Label(
            title_box,
            text="📦 Live Inventory Items",
            font=("Arial", 11, "bold"),
            fg=TEXT_WHITE,
            bg=ACCENT_PURPLE,
            padx=12,
            pady=4,
            cursor="hand2"
        )
        self.btn_tab_items.pack(side="left", padx=(0, 8))
        self.btn_tab_items.bind("<Button-1>", lambda e: self._switch_tab("table"))

        self.btn_tab_ledger = tk.Label(
            title_box,
            text="📜 Movements Audit Ledger",
            font=("Arial", 11),
            fg=TEXT_MUTED,
            bg=BG_CARD_ALT,
            padx=12,
            pady=4,
            cursor="hand2"
        )
        self.btn_tab_ledger.pack(side="left")
        self.btn_tab_ledger.bind("<Button-1>", lambda e: self._switch_tab("ledger"))

        # Right Action Buttons: Stock-In, Stock-Out, Adjust, Export
        act_box = tk.Frame(tb_header, bg=BG_CARD)
        act_box.pack(side="right")

        buttons = [
            ("📥 Stock-In", ACCENT_GREEN, self._open_stock_in_modal),
            ("📤 Stock-Out", ACCENT_ORANGE, self._open_stock_out_modal),
            ("⚖️ Audit Count", "#2563EB", self._open_reconcile_modal),
            ("📊 Export CSV", ACCENT_PURPLE, self.export_ledger_to_csv),
        ]

        for text, col, cmd in buttons:
            btn = tk.Label(
                act_box,
                text=text,
                font=("Arial", 9, "bold"),
                fg=TEXT_WHITE,
                bg=col,
                padx=10,
                pady=4,
                cursor="hand2"
            )
            btn.pack(side="left", padx=4)
            btn.bind("<Button-1>", lambda e, c=cmd: c())

        # Status Filter Row
        filter_row = tk.Frame(self.table_card, bg=BG_CARD, padx=16, pady=4)
        filter_row.pack(fill="x", pady=(0, 8))

        tk.Label(filter_row, text="Status Filter:", font=("Arial", 10), fg=TEXT_MUTED, bg=BG_CARD).pack(side="left", padx=(0, 6))

        self.combo_status = ttk.Combobox(
            filter_row,
            state="readonly",
            values=["All Items", "Low Stock Only", "Adequate Stock Only", "Out of Stock (0)"],
            width=18
        )
        self.combo_status.set("All Items")
        self.combo_status.pack(side="left", padx=(0, 16))
        self.combo_status.bind("<<ComboboxSelected>>", lambda e: self.filter_monitor())

        self.lbl_record_count = tk.Label(filter_row, text="Displaying: 0 products", font=("Arial", 9), fg=TEXT_MUTED, bg=BG_CARD)
        self.lbl_record_count.pack(side="right")

        # Treeview Table
        tree_frame = tk.Frame(self.table_card, bg=BG_CARD, padx=16, pady=4)
        tree_frame.pack(fill="x", pady=(0, 14))

        # Configure Dark Table Style
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "DarkInv.Treeview",
            background="#141A26",
            foreground=TEXT_WHITE,
            fieldbackground="#141A26",
            rowheight=26,
            font=("Arial", 10),
            borderwidth=0
        )
        style.configure(
            "DarkInv.Treeview.Heading",
            background="#1E2838",
            foreground=TEXT_WHITE,
            relief="flat",
            font=("Arial", 10, "bold"),
            padding=[6, 5]
        )
        style.map("DarkInv.Treeview", background=[("selected", ACCENT_PURPLE)])

        cols = ("id", "name", "category", "stock", "min", "price", "val", "status")
        self.tree_items = ttk.Treeview(
            tree_frame,
            columns=cols,
            show="headings",
            height=7,
            style="DarkInv.Treeview"
        )

        headers = [
            ("id", "Item ID", 80),
            ("name", "Product Name", 190),
            ("category", "Category", 130),
            ("stock", "Current Stock", 90),
            ("min", "Min Stock", 80),
            ("price", "Unit Price (₹)", 95),
            ("val", "Stock Valuation (₹)", 115),
            ("status", "Status", 100),
        ]

        for col_id, col_text, col_width in headers:
            self.tree_items.heading(col_id, text=col_text)
            self.tree_items.column(col_id, width=col_width, anchor="center" if col_id in ("id", "stock", "min", "status") else "w")

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_items.yview)
        self.tree_items.configure(yscrollcommand=tree_scroll.set)

        self.tree_items.pack(side="left", fill="x", expand=True)
        tree_scroll.pack(side="right", fill="y")

    def _switch_tab(self, tab_name: str):
        """Switches between Items Table and Ledger Table."""
        if tab_name == "dashboard" or tab_name == "table":
            self.btn_tab_items.configure(bg=ACCENT_PURPLE, fg=TEXT_WHITE)
            self.btn_tab_ledger.configure(bg=BG_CARD_ALT, fg=TEXT_MUTED)
            self.populate_items_table()
        else:
            self.btn_tab_items.configure(bg=BG_CARD_ALT, fg=TEXT_MUTED)
            self.btn_tab_ledger.configure(bg=ACCENT_PURPLE, fg=TEXT_WHITE)
            self.populate_movements_table()

    # =========================================================================
    # DATA LOADING & FILTERING
    # =========================================================================

    def load_data(self):
        """Loads live datasets from StorageManager and updates KPIs."""
        try:
            self.df_products = self.storage.get_products()
            self.df_movements = self.storage.get_stock_movements()
        except Exception as e:
            logger.warning(f"Error loading datasets: {e}")
            self.df_products = pd.DataFrame()
            self.df_movements = pd.DataFrame()

        self.populate_items_table()

        # Update KPI cards if datasets are loaded
        if not self.df_products.empty:
            total_items = len(self.df_products)
            categories = self.df_products["category"].nunique() if "category" in self.df_products.columns else 156
            if "Total Items" in self.kpi_value_labels:
                self.kpi_value_labels["Total Items"].configure(text=f"{total_items:,}")
            if "Categories" in self.kpi_value_labels:
                self.kpi_value_labels["Categories"].configure(text=f"{categories:,}")

    def populate_items_table(self):
        """Fills the dark Treeview table with current product stock."""
        for item in self.tree_items.get_children():
            self.tree_items.delete(item)

        if self.df_products.empty:
            return

        search = self.entry_search.get().strip().lower()
        if search == "search...":
            search = ""
        status_filter = self.combo_status.get()

        displayed_count = 0

        for _, row in self.df_products.iterrows():
            pid = str(row.get("product_id", ""))
            name = str(row.get("product_name", ""))
            cat = str(row.get("category", "General"))
            stock = safe_int(row.get("stock_quantity", row.get("quantity", 0)))
            min_stk = safe_int(row.get("minimum_stock", 10))
            price = safe_float(row.get("selling_price", row.get("purchase_price", 0.0)))
            val = stock * price

            # Status classification
            if stock == 0:
                status_str = "Out of Stock"
            elif stock <= min_stk:
                status_str = "Low Stock"
            else:
                status_str = "Adequate"

            # Apply Search Filter
            if search and search not in pid.lower() and search not in name.lower() and search not in cat.lower():
                continue

            # Apply Status Filter
            if status_filter == "Low Stock Only" and status_str != "Low Stock":
                continue
            if status_filter == "Adequate Stock Only" and status_str != "Adequate":
                continue
            if status_filter == "Out of Stock (0)" and status_str != "Out of Stock":
                continue

            self.tree_items.insert(
                "",
                "end",
                values=(
                    pid,
                    name,
                    cat,
                    stock,
                    min_stk,
                    f"₹{price:,.2f}",
                    f"₹{val:,.2f}",
                    status_str
                )
            )
            displayed_count += 1

        self.lbl_record_count.configure(text=f"Displaying: {displayed_count} items")

    def populate_movements_table(self):
        """Displays recent audit ledger movements."""
        for item in self.tree_items.get_children():
            self.tree_items.delete(item)

        if self.df_movements.empty:
            return

        for _, row in self.df_movements.tail(50).iterrows():
            mid = str(row.get("movement_id", ""))
            pid = str(row.get("product_id", ""))
            mtype = str(row.get("movement_type", ""))
            qty_chg = safe_int(row.get("quantity_change", 0))
            ts = str(row.get("timestamp", ""))
            notes = str(row.get("notes", ""))

            self.tree_items.insert(
                "",
                "end",
                values=(
                    mid,
                    pid,
                    mtype,
                    f"{qty_chg:+d}",
                    "-",
                    ts,
                    "-",
                    notes
                )
            )
        self.lbl_record_count.configure(text=f"Displaying: {len(self.df_movements)} movements")

    def filter_monitor(self):
        """Triggered upon search keystroke or status filter change."""
        self.populate_items_table()

    # =========================================================================
    # MODALS & OPERATIONAL ACTIONS
    # =========================================================================

    def _show_info_modal(self, title: str, message: str):
        """Displays informative confirmation modal."""
        messagebox.showinfo(title, f"FactoryFlow: {message}", parent=self)

    def _open_stock_in_modal(self):
        """Opens Stock-In dialog."""
        self._build_stock_dialog("Stock-In (Purchase Receipt)", "PURCHASE_RECEIPT", is_deduction=False)

    def _open_stock_out_modal(self):
        """Opens Stock-Out write-off dialog."""
        self._build_stock_dialog("Stock-Out (Damage Write-off)", "DAMAGED_WRITE_OFF", is_deduction=True)

    def _build_stock_dialog(self, title: str, mov_type: str, is_deduction: bool):
        """Interactive modal dialog for stock movement."""
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.geometry("400x320")
        dlg.configure(bg=BG_CARD)
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text=title, font=("Arial", 14, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(pady=(16, 10))

        prods = self.storage.get_products()
        prod_names = [f"{r['product_id']} - {r['product_name']}" for _, r in prods.iterrows()]

        tk.Label(dlg, text="Select Product:", font=("Arial", 10), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", padx=30)
        combo = ttk.Combobox(dlg, values=prod_names, state="readonly", width=36)
        if prod_names: combo.set(prod_names[0])
        combo.pack(padx=30, pady=(2, 10))

        tk.Label(dlg, text="Quantity Change:", font=("Arial", 10), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", padx=30)
        entry_qty = tk.Entry(dlg, font=("Arial", 11), bg="#141A26", fg=TEXT_WHITE, insertbackground=TEXT_WHITE)
        entry_qty.pack(fill="x", padx=30, pady=(2, 10))
        entry_qty.insert(0, "10")

        tk.Label(dlg, text="Notes / Reason:", font=("Arial", 10), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", padx=30)
        entry_notes = tk.Entry(dlg, font=("Arial", 11), bg="#141A26", fg=TEXT_WHITE, insertbackground=TEXT_WHITE)
        entry_notes.pack(fill="x", padx=30, pady=(2, 16))
        entry_notes.insert(0, "Restock delivery" if not is_deduction else "Damaged batch write-off")

        def submit():
            sel = combo.get()
            if not sel: return
            pid = sel.split(" - ")[0]
            try:
                qty = int(entry_qty.get().strip())
                if qty <= 0: raise ValueError()
            except ValueError:
                messagebox.showerror("Error", "Quantity must be a positive integer.", parent=dlg)
                return

            chg = -qty if is_deduction else qty
            ok, msg = self.storage.record_stock_movement(
                product_id=pid,
                movement_type=mov_type,
                quantity_change=chg,
                notes=entry_notes.get().strip()
            )
            if ok:
                messagebox.showinfo("Success", msg, parent=dlg)
                dlg.destroy()
                self.load_data()
                if self.on_inventory_changed:
                    self.on_inventory_changed()
            else:
                messagebox.showerror("Error", msg, parent=dlg)

        btn_submit = tk.Button(
            dlg,
            text="Confirm Operation",
            font=("Arial", 11, "bold"),
            fg=TEXT_WHITE,
            bg=ACCENT_GREEN if not is_deduction else ACCENT_RED,
            relief="flat",
            command=submit
        )
        btn_submit.pack(fill="x", padx=30, pady=(0, 10))

    def _open_reconcile_modal(self):
        """Opens physical audit stock adjustment dialog."""
        dlg = tk.Toplevel(self)
        dlg.title("Physical Audit Adjustment")
        dlg.geometry("400x300")
        dlg.configure(bg=BG_CARD)
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text="Physical Shelf Audit Count", font=("Arial", 14, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(pady=(16, 10))

        prods = self.storage.get_products()
        prod_names = [f"{r['product_id']} - {r['product_name']}" for _, r in prods.iterrows()]

        tk.Label(dlg, text="Select Product:", font=("Arial", 10), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", padx=30)
        combo = ttk.Combobox(dlg, values=prod_names, state="readonly", width=36)
        if prod_names: combo.set(prod_names[0])
        combo.pack(padx=30, pady=(2, 10))

        tk.Label(dlg, text="Actual Physical Count:", font=("Arial", 10), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", padx=30)
        entry_cnt = tk.Entry(dlg, font=("Arial", 11), bg="#141A26", fg=TEXT_WHITE, insertbackground=TEXT_WHITE)
        entry_cnt.pack(fill="x", padx=30, pady=(2, 10))

        tk.Label(dlg, text="Audit Reason:", font=("Arial", 10), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", padx=30)
        entry_rsn = tk.Entry(dlg, font=("Arial", 11), bg="#141A26", fg=TEXT_WHITE, insertbackground=TEXT_WHITE)
        entry_rsn.pack(fill="x", padx=30, pady=(2, 16))
        entry_rsn.insert(0, "Physical shelf reconciliation audit")

        def submit():
            sel = combo.get()
            if not sel: return
            pid = sel.split(" - ")[0]
            try:
                cnt = int(entry_cnt.get().strip())
                if cnt < 0: raise ValueError()
            except ValueError:
                messagebox.showerror("Error", "Count must be a non-negative integer.", parent=dlg)
                return

            ok, msg = self.storage.manual_stock_reconciliation(
                product_id=pid,
                physical_count=cnt,
                reason=entry_rsn.get().strip()
            )
            if ok:
                messagebox.showinfo("Success", msg, parent=dlg)
                dlg.destroy()
                self.load_data()
                if self.on_inventory_changed:
                    self.on_inventory_changed()
            else:
                messagebox.showerror("Error", msg, parent=dlg)

        btn_submit = tk.Button(
            dlg,
            text="Reconcile Inventory",
            font=("Arial", 11, "bold"),
            fg=TEXT_WHITE,
            bg=ACCENT_BLUE,
            relief="flat",
            command=submit
        )
        btn_submit.pack(fill="x", padx=30, pady=(0, 10))

    def _open_add_product_modal(self):
        """Quick Action: Add Item modal."""
        dlg = tk.Toplevel(self)
        dlg.title("Add New Inventory Item")
        dlg.geometry("420x400")
        dlg.configure(bg=BG_CARD)
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text="Add New Item", font=("Arial", 14, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(pady=(16, 12))

        fields = [
            ("Product Name", "entry_name", "Organic Apples"),
            ("Category", "entry_cat", "Fresh Produce"),
            ("Stock Quantity", "entry_qty", "50"),
            ("Selling Price (₹)", "entry_price", "3.99"),
        ]

        entries = {}
        for lbl_txt, var_name, default_val in fields:
            tk.Label(dlg, text=lbl_txt, font=("Arial", 10), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", padx=30)
            e = tk.Entry(dlg, font=("Arial", 10), bg="#141A26", fg=TEXT_WHITE, insertbackground=TEXT_WHITE)
            e.pack(fill="x", padx=30, pady=(2, 8))
            e.insert(0, default_val)
            entries[var_name] = e

        def submit():
            name = entries["entry_name"].get().strip()
            cat = entries["entry_cat"].get().strip()
            qty = safe_int(entries["entry_qty"].get().strip(), 0)
            price = safe_float(entries["entry_price"].get().strip(), 0.0)

            if not name:
                messagebox.showerror("Error", "Product Name is required.", parent=dlg)
                return

            new_pid = f"PRD-{len(self.df_products) + 1:04d}"
            ok, msg = self.storage.create_product({
                "product_id": new_pid,
                "product_name": name,
                "category": cat,
                "stock_quantity": qty,
                "selling_price": price,
                "minimum_stock": 10,
                "purchase_price": price * 0.7
            })
            if ok:
                messagebox.showinfo("Success", f"Item created: {new_pid}", parent=dlg)
                dlg.destroy()
                self.load_data()
                if self.on_inventory_changed:
                    self.on_inventory_changed()
            else:
                messagebox.showerror("Error", msg, parent=dlg)

        tk.Button(
            dlg,
            text="Save Item",
            font=("Arial", 11, "bold"),
            fg=TEXT_WHITE,
            bg=ACCENT_PURPLE,
            relief="flat",
            command=submit
        ).pack(fill="x", padx=30, pady=(10, 0))

    def export_ledger_to_csv(self):
        """Exports stock movement audit ledger to CSV."""
        if self.df_movements.empty:
            messagebox.showinfo("Export", "No stock movements to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"stock_movements_{date.today().strftime('%Y%m%d')}.csv"
        )
        if not file_path:
            return

        ok, msg = export_dataframe_to_csv(self.df_movements, file_path)
        if ok:
            messagebox.showinfo("Export Complete", msg)
        else:
            messagebox.showerror("Export Failed", msg)


# =============================================================================
# STANDALONE LAUNCHER (PAGE 2 PRESENTATION MODE)
# =============================================================================

class StandaloneInventoryApp(tk.Tk):
    """
    Dedicated Standalone Window matching the reference slide:
    - Deep dark background canvas (#0A0D10)
    - Top Header: 'PAGE 2' green pill, 'CRUD Operations Dashboard' title,
      and 'Central navigation hub' subtitle.
    - Central rounded FactoryFlow Inventory Dashboard container.
    """

    def __init__(self):
        super().__init__()

        self.title("CRUD Operations Dashboard | FactoryFlow")
        self.geometry("1280x820")
        self.minsize(1050, 680)
        self.configure(bg=BG_CANVAS)

        self._build_presentation_ui()

    def _build_presentation_ui(self):
        # 1. Top Header
        header = tk.Frame(self, bg=BG_CANVAS)
        header.pack(side="top", pady=(14, 8))

        # Green Pill Badge: 'PAGE 2'
        pill = tk.Label(
            header,
            text="PAGE 2",
            font=("Arial", 10, "bold"),
            fg="#22C55E",
            bg="#0D2818",
            padx=14,
            pady=3
        )
        pill.pack(pady=(0, 4))

        # Title: 'CRUD Operations Dashboard'
        tk.Label(
            header,
            text="CRUD Operations Dashboard",
            font=("Arial", 18, "bold"),
            fg=TEXT_WHITE,
            bg=BG_CANVAS
        ).pack(pady=(0, 2))

        # Subtitle: 'Central navigation hub'
        tk.Label(
            header,
            text="Central navigation hub",
            font=("Arial", 11),
            fg=TEXT_MUTED,
            bg=BG_CANVAS
        ).pack(pady=(0, 4))

        # 2. Main Rounded FactoryFlow Application Window
        app_wrapper = tk.Frame(
            self,
            bg=BG_APP,
            bd=1,
            relief="solid",
            highlightthickness=0
        )
        app_wrapper.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # Instantiate the FactoryFlow Inventory Management View inside the wrapper
        self.inventory_view = InventoryManagementView(app_wrapper)
        self.inventory_view.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = StandaloneInventoryApp()
    app.mainloop()
