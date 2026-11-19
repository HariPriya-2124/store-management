"""
Screen 1: Supermarket Home Page for Store Management System.
Matches the top screen of the primary UI/UX design reference:
- Full-screen supermarket storefront illustration as background.
- Prominent heading in top-left sky: 'CRUD OPERATIONS ON STORE MANAGEMENT SYSTEM'.
- Centered interactive 'Login / Register' button situated directly on the supermarket entrance.
- High interactivity: hover animations, hand cursor, demo access, resize reactivity.
"""

import tkinter as tk
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PIL import Image, ImageTk

from config import FONT_FAMILY, FONTS, STOREFRONT_IMG_PATH, THEME
from utils.logger import get_logger

logger = get_logger("HomeScreen")


class SupermarketHomeScreen(tk.Frame):
    """
    Screen 1: Welcome / Supermarket Storefront Landing Page.
    Faithfully implements Screen 1 of the reference design.
    """

    def __init__(self, parent: tk.Widget, on_login_clicked=None, on_register_clicked=None, on_guest_clicked=None):
        super().__init__(parent, bg="#E0F7FA")
        self.on_login_clicked = on_login_clicked
        self.on_register_clicked = on_register_clicked
        self.on_guest_clicked = on_guest_clicked

        self.bg_photo = None
        self._raw_img = None

        if STOREFRONT_IMG_PATH.exists():
            try:
                self._raw_img = Image.open(STOREFRONT_IMG_PATH).convert("RGB")
            except Exception as e:
                logger.warning(f"Could not load storefront image: {e}")

        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Full-window Canvas where the supermarket storefront image is drawn
        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#E0F7FA")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Initial immediate background rendering so screen is never blank
        self._draw_background(1300, 840)

        # Draw the prominent title directly onto the sky centered
        self.canvas.create_text(
            650, 42,
            text="CRUD OPERATIONS ON STORE MANAGEMENT SYSTEM",
            font=(FONT_FAMILY, 20, "bold"),
            fill="#05204A",
            anchor="center",
            tags="sky_title"
        )

        # Create Entrance Door Interactive Card
        self.entrance_frame = tk.Frame(self.canvas, bg="#0077B6", bd=2, relief="ridge", padx=8, pady=8)

        # Main Login / Register Button
        self.btn_main = tk.Button(
            self.entrance_frame,
            text="🚪  LOGIN / REGISTER",
            command=self._handle_login,
            font=("Segoe UI", 12, "bold") if tk.TkVersion >= 8.6 else FONTS["body_bold"],
            bg="#00B4D8",
            fg="#FFFFFF",
            activebackground="#028090",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2"
        )
        self.btn_main.pack(fill="x", pady=(0, 4))
        self._bind_hover(self.btn_main, "#00B4D8", "#028090")

        # Quick Demo Instant Access Button
        self.btn_demo = tk.Button(
            self.entrance_frame,
            text="⚡ Quick Demo Access",
            command=self._handle_guest,
            font=FONTS["caption_bold"],
            bg="#D8F3DC",
            fg="#1B4332",
            activebackground="#B7E4C7",
            activeforeground="#1B4332",
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2"
        )
        self.btn_demo.pack(fill="x")
        self._bind_hover(self.btn_demo, "#D8F3DC", "#B7E4C7")

        # Window ID on canvas for dynamic positioning
        self.window_id = self.canvas.create_window(650, 485, window=self.entrance_frame, anchor="center")

        # Bind configure directly on canvas
        self.canvas.bind("<Configure>", self._on_resize)

        # Bind canvas click so clicking anywhere near the door triggers login
        self.canvas.bind("<Button-1>", self._on_canvas_click)

    def _draw_background(self, w: int, h: int):
        """Renders the background image onto canvas with strong reference retention."""
        if not self._raw_img:
            return
        try:
            w = max(w, 200)
            h = max(h, 200)
            resized = self._raw_img.resize((w, h), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(resized)
            self.canvas.bg_photo = self.bg_photo  # retain reference on widget

            self.canvas.delete("bg_img")
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw", tags="bg_img")
            self.canvas.tag_lower("bg_img")
        except Exception as e:
            logger.warning(f"Error drawing storefront background: {e}")

    def _bind_hover(self, widget: tk.Button, normal_bg: str, hover_bg: str):
        """Adds smooth interactive hover feedback to buttons."""
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))

    def _on_canvas_click(self, event):
        """Clicking on or near the central doors opens the login page."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        dx_min, dx_max = w * 0.38, w * 0.62
        dy_min, dy_max = h * 0.45, h * 0.80
        if dx_min <= event.x <= dx_max and dy_min <= event.y <= dy_max:
            self._handle_login()

    def _on_resize(self, event):
        """Handles canvas resizing and repositions entrance button accurately."""
        if event.widget != self.canvas:
            return
        w, h = event.width, event.height
        if w < 100 or h < 100:
            return

        self._draw_background(w, h)

        # Re-position title and door entrance button
        self.canvas.coords("sky_title", w // 2, 42)
        door_x = w // 2
        door_y = int(h * 0.58)
        self.canvas.coords(self.window_id, door_x, door_y)

    def _handle_login(self):
        if self.on_login_clicked:
            self.on_login_clicked()

    def _handle_register(self):
        if self.on_register_clicked:
            self.on_register_clicked()

    def _handle_guest(self):
        if self.on_guest_clicked:
            self.on_guest_clicked()
