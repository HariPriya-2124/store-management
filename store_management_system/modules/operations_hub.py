"""
Page 2: Main CRUD Operations Page for Store Management System.
Features:
- Supermarket aisle & counter background illustration (hub.png).
- Smiling mascot character with 'Yeah!' neon splash on the right.
- Central column of the 6 core supermarket operation buttons matching reference:
    1. Create Operation
    2. Retrieve Operation
    3. Update Operation
    4. Delete Operation
    5. Expiry Date Operation
    6. Send SMS Operation
- High interactivity: smooth button hover animations, live KPI metrics from datasets,
  top navigation bar with User Profile and Logout,
  and bottom dock for extended modules (POS Sales, Inventory, Analytics, Suppliers, Settings).
"""

from datetime import datetime
import tkinter as tk
from tkinter import ttk
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PIL import Image, ImageTk
import pandas as pd

from config import AISLE_HUB_IMG_PATH, ASSETS_DIR, FONTS, THEME
from database.storage_manager import StorageManager
from utils.helpers import format_currency, format_quantity, safe_float, safe_int
from utils.logger import get_logger

logger = get_logger("OperationsHub")


class OperationsHubView(tk.Frame):
    """
    Page 2: Main CRUD Operations Hub.
    """

    def __init__(self, parent: tk.Widget, storage: StorageManager, nav_callback=None, user_info=None):
        super().__init__(parent, bg="#FFF3E0")
        self.storage = storage
        self.nav_callback = nav_callback
        self.user_info = user_info or {"name": "Store Administrator", "role": "Super Admin"}

        self.bg_photo = None
        self._bg_photo = None
        self._prev_bg_photo = None
        self._raw_img = None
        self._last_bg_size = (0, 0)
        self._resize_job = None
        self.btn_images = {}

        # Search for high-quality supermarket background candidates in assets
        candidates = [
            AISLE_HUB_IMG_PATH,
            ASSETS_DIR / "supermarket_bg.jpg",
            ASSETS_DIR / "supermarket_aisle_photoreal.png",
            ASSETS_DIR / "supermarket_bg_clean.png",
            ASSETS_DIR / "hub.png",
            ASSETS_DIR / "supermarket_aisle_hub.png",
        ]
        for c_path in candidates:
            if c_path and c_path.exists():
                try:
                    self._raw_img = Image.open(c_path).convert("RGB")
                    logger.info(f"Loaded hub background image from: {c_path.name}")
                    break
                except Exception as e:
                    logger.warning(f"Could not load image candidate {c_path}: {e}")

        self._load_button_images()
        self._build_ui()
        self.refresh_metrics()

    def _load_button_images(self):
        """Loads modern distinct card images for the 6 operations buttons."""
        btn_dir = ASSETS_DIR / "buttons"
        img_keys = [
            ("op_create", "btn_create.png", "btn_create_hover.png"),
            ("op_read",   "btn_read.png",   "btn_read_hover.png"),
            ("op_update", "btn_update.png", "btn_update_hover.png"),
            ("op_delete", "btn_delete.png", "btn_delete_hover.png"),
            ("op_expiry", "btn_expiry.png", "btn_expiry_hover.png"),
            ("op_sms",    "btn_sms.png",    "btn_sms_hover.png"),
        ]
        for key, n_img, h_img in img_keys:
            n_path = btn_dir / n_img
            h_path = btn_dir / h_img
            if n_path.exists() and h_path.exists():
                try:
                    self.btn_images[key] = (
                        ImageTk.PhotoImage(Image.open(n_path), master=self),
                        ImageTk.PhotoImage(Image.open(h_path), master=self)
                    )
                except Exception as e:
                    logger.warning(f"Error loading button image {key}: {e}")

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Full-window Canvas where the aisle background image is drawn
        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#FFF3E0")
        self.canvas.pack(fill="both", expand=True)

        # Draw background immediately so screen is never blank
        self._draw_background(1300, 840)

        # ---------------------------------------------------------------------
        # 1. TOP HEADER BAR
        # ---------------------------------------------------------------------
        self.top_bar = tk.Frame(self.canvas, bg="#05668D", padx=20, pady=7)

        title_box = tk.Frame(self.top_bar, bg="#05668D")
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="🛒 CRUD OPERATIONS ON STORE MANAGEMENT SYSTEM",
            font=("Segoe UI", 12, "bold") if tk.TkVersion >= 8.6 else FONTS["body_bold"],
            bg="#05668D",
            fg="#FFFFFF"
        ).pack(side="left", padx=(0, 10))

        right_box = tk.Frame(self.top_bar, bg="#05668D")
        right_box.pack(side="right")

        user_name = self.user_info.get("name", "Store Administrator")
        user_role = self.user_info.get("role", "Manager")

        tk.Label(
            right_box,
            text=f"👤 {user_name} ({user_role})",
            font=FONTS["caption_bold"],
            bg="#028090",
            fg="#FFFFFF",
            padx=10,
            pady=3
        ).pack(side="left", padx=8)

        btn_logout = tk.Button(
            right_box,
            text="🔓 Logout",
            command=lambda: self._navigate_to("logout"),
            font=FONTS["caption_bold"],
            bg="#E76F51",
            fg="#FFFFFF",
            activebackground="#D9534F",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=12,
            pady=3,
            cursor="hand2"
        )
        btn_logout.pack(side="left")
        self._bind_hover(btn_logout, "#E76F51", "#D9534F")

        self.top_bar_window = self.canvas.create_window(0, 0, window=self.top_bar, anchor="nw")

        # ---------------------------------------------------------------------
        # 2. THE 6 MAIN OPERATIONS BUTTONS
        # ---------------------------------------------------------------------
        self.btn_col_frame = tk.Frame(self.canvas, bg="", bd=0)

        # The 6 core operations:
        self.operations = [
            ("op_create", "➕  Create Operation",      "#00B4D8", "#028090"),
            ("op_read",   "📋  Retrieve Operation",    "#00B4D8", "#028090"),
            ("op_update", "🔄  Update Operation",      "#00B4D8", "#028090"),
            ("op_delete", "🗑️  Delete Operation",      "#00B4D8", "#028090"),
            ("op_expiry", "⚠️  Expiry Date Operation", "#00B4D8", "#028090"),
            ("op_sms",    "📱  Send SMS Notification", "#00B4D8", "#028090"),
        ]

        self.op_buttons = []
        for nav_key, label_text, norm_col, hov_col in self.operations:
            if nav_key in self.btn_images:
                norm_img, hov_img = self.btn_images[nav_key]
                btn = tk.Button(
                    self.btn_col_frame,
                    image=norm_img,
                    text=label_text,
                    compound="none",
                    command=lambda k=nav_key: self._navigate_to(k),
                    relief="flat",
                    bd=0,
                    highlightthickness=0,
                    bg="#FFF3E0",
                    activebackground="#FFF3E0",
                    cursor="hand2"
                )
                btn.norm_img = norm_img
                btn.hov_img = hov_img
                btn.bind("<Enter>", lambda e, b=btn, hi=hov_img: b.config(image=hi))
                btn.bind("<Leave>", lambda e, b=btn, ni=norm_img: b.config(image=ni))
                btn.pack(pady=5)
                self.op_buttons.append(btn)
            else:
                btn = tk.Button(
                    self.btn_col_frame,
                    text=label_text,
                    command=lambda k=nav_key: self._navigate_to(k),
                    font=("Segoe UI", 12, "bold") if tk.TkVersion >= 8.6 else FONTS["body_bold"],
                    bg=norm_col,
                    fg="#0F172A",
                    activebackground=hov_col,
                    activeforeground="#028090",
                    relief="flat",
                    bd=1,
                    width=26,
                    pady=8,
                    cursor="hand2"
                )
                btn.pack(pady=5)
                self._bind_hover(btn, norm_col, hov_col)
                self.op_buttons.append(btn)

        self.btn_col_window = self.canvas.create_window(500, 380, window=self.btn_col_frame, anchor="center")

        # ---------------------------------------------------------------------
        # 3. BOTTOM EXTENDED MODULES DOCK & KPI BAR
        # ---------------------------------------------------------------------
        self.bottom_dock = tk.Frame(self.canvas, bg="#05668D", padx=15, pady=6)

        dock_buttons = [
            ("sales",     "🛒 POS Sales",          "#2A9D8F"),
            ("inventory", "📦 Inventory Movements", "#00B4D8"),
            ("analytics", "📊 Analytics & BI",     "#52B788"),
            ("suppliers", "🏢 Suppliers",          "#E76F51"),
            ("settings",  "⚙️ Backups & Settings", "#028090"),
        ]

        for mod_key, mod_label, mod_color in dock_buttons:
            d_btn = tk.Button(
                self.bottom_dock,
                text=mod_label,
                command=lambda k=mod_key: self._navigate_to(k),
                font=FONTS["caption_bold"],
                bg=mod_color,
                fg="#0F172A",
                activebackground="#028090",
                activeforeground="#028090",
                relief="flat",
                bd=0,
                padx=10,
                pady=4,
                cursor="hand2"
            )
            d_btn.pack(side="left", padx=4)
            self._bind_hover(d_btn, mod_color, "#028090")

        self.lbl_kpi = tk.Label(
            self.bottom_dock,
            text="Products: -- | Sales: -- | Expiry Alerts: --",
            font=FONTS["caption_bold"],
            bg="#028090",
            fg="#FFFFFF",
            padx=10,
            pady=3
        )
        self.lbl_kpi.pack(side="right", padx=6)

        self.bottom_dock_window = self.canvas.create_window(0, 720, window=self.bottom_dock, anchor="sw")

        # Bind configure & map directly on canvas
        self.canvas.bind("<Configure>", self._on_resize)
        self.bind("<Map>", self._on_map)

    def _on_map(self, event):
        """Triggered when hub is mapped onto Cocoa display surface."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 50 and h > 50:
            self._draw_background(w, h)
            self.canvas.itemconfig(self.top_bar_window, width=w)
            col_x = int(w * 0.48)
            col_y = int(h * 0.48)
            self.canvas.coords(self.btn_col_window, col_x, col_y)
            self.canvas.coords(self.bottom_dock_window, 0, h)
            self.canvas.itemconfig(self.bottom_dock_window, width=w)

    def _draw_background(self, w: int, h: int):
        """Draws background image onto canvas with strong reference retention."""
        if not self._raw_img:
            return
        try:
            w = max(w, 200)
            h = max(h, 200)
            resized = self._raw_img.resize((w, h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(resized, master=self.canvas)
            # Retain both new and previous photo references to prevent premature Tcl GC
            self._prev_bg_photo = getattr(self, "_bg_photo", None)
            self._bg_photo = photo
            self.bg_photo = photo
            self.canvas.bg_photo = photo

            if self.canvas.find_withtag("bg_img"):
                self.canvas.itemconfig("bg_img", image=self._bg_photo)
            else:
                self.canvas.create_image(0, 0, image=self._bg_photo, anchor="nw", tags="bg_img")
            self.canvas.tag_lower("bg_img")
            if hasattr(self, "top_bar_window"):
                self.canvas.tag_raise(self.top_bar_window)
            if hasattr(self, "btn_col_window"):
                self.canvas.tag_raise(self.btn_col_window)
            if hasattr(self, "bottom_dock_window"):
                self.canvas.tag_raise(self.bottom_dock_window)
        except Exception as e:
            logger.warning(f"Error drawing aisle background: {e}")

    def _bind_hover(self, widget: tk.Button, normal_bg: str, hover_bg: str):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg, fg="#028090"))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg, fg="#0F172A"))

    def _on_resize(self, event):
        if event.widget != self.canvas:
            return
        w, h = event.width, event.height
        if w < 10 or h < 10:
            return

        # Keep child windows properly aligned immediately
        self.canvas.itemconfig(self.top_bar_window, width=w)
        col_x = int(w * 0.48)
        col_y = int(h * 0.48)
        self.canvas.coords(self.btn_col_window, col_x, col_y)
        self.canvas.coords(self.bottom_dock_window, 0, h)
        self.canvas.itemconfig(self.bottom_dock_window, width=w)
        self.canvas.tag_raise(self.top_bar_window)
        self.canvas.tag_raise(self.btn_col_window)
        self.canvas.tag_raise(self.bottom_dock_window)

        # Avoid redundant PIL resizing on micro-movements
        if abs(w - self._last_bg_size[0]) < 15 and abs(h - self._last_bg_size[1]) < 15:
            return

        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass

        self._resize_job = self.after(30, lambda: self._perform_debounced_bg_resize(w, h))

    def _perform_debounced_bg_resize(self, w: int, h: int):
        self._resize_job = None
        self._last_bg_size = (w, h)
        self._draw_background(w, h)

    def refresh_metrics(self):
        """Pulls fresh numbers directly from CSV datasets."""
        try:
            df_prod = self.storage.get_products()
            df_sales = self.storage.get_sales()
            df_exp = self.storage.get_expiry_alerts()

            prod_count = len(df_prod) if not df_prod.empty else 0
            sales_count = len(df_sales) if not df_sales.empty else 0
            alert_count = len(df_exp) if not df_exp.empty else 0

            tot_rev = 0.0
            if not df_sales.empty:
                s_amt = pd.to_numeric(df_sales["total_amount"], errors="coerce").fillna(0.0)
                tot_rev = float(s_amt.sum())

            self.lbl_kpi.config(
                text=f"📦 Catalog: {prod_count} items  |  🛒 Sales: {sales_count} (₹{tot_rev:,.2f})  |  ⚠️ Alerts: {alert_count}"
            )
        except Exception as e:
            logger.warning(f"Error refreshing hub KPIs: {e}")

    def _navigate_to(self, key: str):
        if self.nav_callback:
            self.nav_callback(key)
