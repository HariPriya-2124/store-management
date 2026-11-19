"""
Page 1: Login and Registration Page for Store Management System.
Features:
- Supermarket shoppers & storefront background illustration.
- Clean, centered authentication card with interactive Login / Register mode toggling.
- Form validation with informative error messages.
- Real-time password visibility toggle (👁️ / 🔒).
- 1-Click Instant Demo Login for quick testing.
- Successful login automatically navigates to Page 2 (CRUD Operations Hub).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PIL import Image, ImageTk

from config import FONT_FAMILY, FONTS, SHOPPERS_IMG_PATH, SUPERMARKET_IMG_PATH, THEME
from utils.logger import get_logger
from utils.validators import validate_email, validate_non_empty

logger = get_logger("AuthScreen")

# Default pre-configured store users
REGISTERED_USERS = {
    "admin@supermarket.com": {"password": "admin123", "name": "Store Administrator", "role": "Super Admin"},
    "cashier@supermarket.com": {"password": "cashier123", "name": "Sarah Miller", "role": "Senior Cashier"},
    "manager@supermarket.com": {"password": "manager123", "name": "David Clark", "role": "Inventory Manager"},
}


class ElegantButton(tk.Frame):
    """
    Modern pill-shaped or flat button with reliable cross-platform background,
    hover transitions, and support for the standard tk.Button .invoke() method.
    """
    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command=None,
        bg: str = "#028090",
        fg: str = "#FFFFFF",
        hover_bg: str = "#00B4D8",
        font=("Segoe UI", 10, "bold"),
        pady: int = 8,
        border_color: str = None,
        **kwargs
    ):
        super().__init__(
            parent,
            bg=bg,
            cursor="hand2",
            highlightthickness=1 if border_color else 0,
            highlightbackground=border_color or bg
        )
        self.command = command
        self.bg_color = bg
        self.hover_color = hover_bg
        self.border_color = border_color
        self.lbl = tk.Label(
            self,
            text=text,
            font=font,
            fg=fg,
            bg=bg,
            cursor="hand2",
            pady=pady
        )
        self.lbl.pack(fill="both", expand=True)

        for w in (self, self.lbl):
            w.bind("<Enter>", lambda e: self._on_enter())
            w.bind("<Leave>", lambda e: self._on_leave())
            w.bind("<Button-1>", lambda e: self.invoke())

    def _on_enter(self):
        self.config(bg=self.hover_color)
        self.lbl.config(bg=self.hover_color)
        if self.border_color:
            self.config(highlightbackground=self.hover_color)

    def _on_leave(self):
        self.config(bg=self.bg_color)
        self.lbl.config(bg=self.bg_color)
        if self.border_color:
            self.config(highlightbackground=self.border_color)

    def invoke(self):
        if self.command:
            return self.command()

    def config(self, **kwargs):
        if "text" in kwargs:
            self.lbl.config(text=kwargs.pop("text"))
        if "bg" in kwargs:
            self.bg_color = kwargs["bg"]
            self.lbl.config(bg=kwargs["bg"])
        super().config(**kwargs)


class AuthScreen(tk.Frame):
    """
    Page 1: Supermarket Authentication Page (Login & Registration).
    """

    def __init__(self, parent: tk.Widget, on_auth_success=None, initial_mode: str = "login"):
        super().__init__(parent, bg="#C8D1D5")
        self.on_auth_success = on_auth_success
        self.current_mode = initial_mode  # "login" or "register"

        self.bg_photo = None
        self._bg_photo = None
        self._prev_bg_photo = None
        self._last_bg_size = (0, 0)
        self._resize_job = None
        self._raw_img = None
        self._show_pass = False

        # Load shoppers or supermarket background image
        img_path = SHOPPERS_IMG_PATH if SHOPPERS_IMG_PATH.exists() else SUPERMARKET_IMG_PATH
        if img_path.exists():
            try:
                self._raw_img = Image.open(img_path).convert("RGB")
            except Exception as e:
                logger.warning(f"Could not load auth background image: {e}")

        self._build_ui()

    def _build_ui(self):
        # Full-window Canvas where the background image is drawn
        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#C8D1D5")
        self.canvas.pack(fill="both", expand=True)

        # Initial background draw immediately
        self._draw_background(1300, 840)

        # Prominent Title Header centered at top of canvas
        self.canvas.create_text(
            650, 36,
            text="CRUD OPERATIONS ON STORE MANAGEMENT SYSTEM",
            font=(FONT_FAMILY, 20, "bold"),
            fill="#05204A",
            anchor="center",
            tags="auth_title_main"
        )
        self.canvas.create_text(
            650, 66,
            text="ENTERPRISE POINT-OF-SALE, INVENTORY TRACKING & DATA SCIENCE",
            font=(FONT_FAMILY, 10, "bold"),
            fill="#028090",
            anchor="center",
            tags="auth_title_sub"
        )

        # The Authentication Form Card (clean modern floating card)
        self.card = tk.Frame(
            self.canvas,
            bg="#FFFFFF",
            padx=36,
            pady=26,
            highlightbackground="#CBD5E1",
            highlightthickness=1
        )
        self.card_window = self.canvas.create_window(650, 420, window=self.card, anchor="center")
        self.canvas.tag_raise(self.card_window)

        self._render_form_fields()

        # Canvas resize & map listeners
        self.canvas.bind("<Configure>", self._on_resize)
        self.bind("<Map>", self._on_map)

        # Keyboard shortcuts
        self.bind("<Return>", lambda e: self._on_enter_pressed())

    def _on_map(self, event):
        """Triggered when widget is mapped onto Cocoa display surface."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 50 and h > 50:
            self._draw_background(w, h)
            center_x = int(w * 0.50)
            self.canvas.coords("auth_title_main", center_x, 36)
            self.canvas.coords("auth_title_sub", center_x, 66)
            card_x = center_x
            card_y = max(int(h * 0.52), 370)
            self.canvas.coords(self.card_window, card_x, card_y)
            self.canvas.tag_raise(self.card_window)

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
            if hasattr(self, "card_window"):
                self.canvas.tag_raise(self.card_window)
            self.canvas.tag_raise("auth_title_main")
            self.canvas.tag_raise("auth_title_sub")
        except Exception as e:
            logger.warning(f"Error drawing auth background: {e}")

    def _create_elegant_field(
        self,
        parent: tk.Widget,
        label: str,
        icon: str,
        default_val: str = "",
        is_password: bool = False,
        is_combobox: bool = False,
        combo_values: list = None
    ):
        """Creates an elegant floating input container with icon label and active focus highlight."""
        field_container = tk.Frame(parent, bg="#FFFFFF")
        field_container.pack(fill="x", pady=(0, 9))

        # Field Label with Icon
        lbl_box = tk.Frame(field_container, bg="#FFFFFF")
        lbl_box.pack(fill="x", pady=(0, 4))

        tk.Label(
            lbl_box,
            text=f"{icon}  {label}",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#334155"
        ).pack(side="left")

        # Elegant Input Frame
        input_box = tk.Frame(
            field_container,
            bg="#F8FAFC",
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            padx=2,
            pady=2
        )
        input_box.pack(fill="x")

        if is_combobox:
            combo = ttk.Combobox(
                input_box,
                state="readonly",
                values=combo_values or [],
                font=("Segoe UI", 10)
            )
            if default_val and default_val in (combo_values or []):
                combo.set(default_val)
            elif combo_values:
                combo.set(combo_values[0])
            combo.pack(fill="both", expand=True, padx=6, pady=5)
            return combo

        entry = tk.Entry(
            input_box,
            font=("Segoe UI", 11),
            bg="#F8FAFC",
            fg="#0F172A",
            bd=0,
            relief="flat",
            highlightthickness=0,
            insertbackground="#028090"
        )
        if is_password:
            entry.config(show="•" if not self._show_pass else "")

        entry.pack(side="left", fill="both", expand=True, padx=(10, 4), pady=6)
        if default_val:
            entry.insert(0, default_val)

        btn_eye = None
        if is_password:
            self.btn_eye = tk.Label(
                input_box,
                text="👁️" if not self._show_pass else "🔒",
                font=("Segoe UI", 12),
                bg="#F8FAFC",
                fg="#64748B",
                cursor="hand2",
                padx=8,
                pady=4
            )
            self.btn_eye.pack(side="right")

            def on_eye_click(e=None):
                self._toggle_password_visibility()

            self.btn_eye.bind("<Button-1>", on_eye_click)
            self.btn_eye.bind("<Enter>", lambda e: self.btn_eye.config(fg="#028090"))
            self.btn_eye.bind("<Leave>", lambda e: self.btn_eye.config(fg="#64748B" if not self._show_pass else "#028090"))

        def on_focus_in(event):
            input_box.config(highlightbackground="#028090", highlightthickness=2, bg="#FFFFFF")
            entry.config(bg="#FFFFFF")
            if is_password and hasattr(self, "btn_eye"):
                self.btn_eye.config(bg="#FFFFFF")

        def on_focus_out(event):
            input_box.config(highlightbackground="#CBD5E1", highlightthickness=1, bg="#F8FAFC")
            entry.config(bg="#F8FAFC")
            if is_password and hasattr(self, "btn_eye"):
                self.btn_eye.config(bg="#F8FAFC")

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

        return entry

    def _render_form_fields(self):
        """Builds modern, elegant input fields and buttons for current mode."""
        for widget in self.card.winfo_children():
            widget.destroy()

        is_login = self.current_mode == "login"

        # 1. Top Brand Pill Badge
        badge_strip = tk.Frame(self.card, bg="#FFFFFF")
        badge_strip.pack(fill="x", pady=(0, 6))

        tk.Label(
            badge_strip,
            text="🛒 STORE MANAGEMENT SYSTEM",
            font=("Segoe UI", 9, "bold"),
            bg="#E0F2FE",
            fg="#0369A1",
            padx=10,
            pady=3
        ).pack(side="left")

        # 2. Main Title & Subtitle
        title_text = "Store User Sign In" if is_login else "Register New Cashier"
        tk.Label(
            self.card,
            text=title_text,
            font=("Segoe UI", 16, "bold"),
            bg="#FFFFFF",
            fg="#0F172A"
        ).pack(anchor="w", pady=(2, 2))

        sub_text = "Sign in to access your CRUD operations hub" if is_login else "Create staff credentials for store operations"
        tk.Label(
            self.card,
            text=sub_text,
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#64748B"
        ).pack(anchor="w", pady=(0, 10))

        # 3. Modern Segmented Tab Switcher [ Sign In ] [ Register ]
        tab_frame = tk.Frame(self.card, bg="#F1F5F9", padx=3, pady=3)
        tab_frame.pack(fill="x", pady=(0, 12))
        tab_frame.columnconfigure(0, weight=1)
        tab_frame.columnconfigure(1, weight=1)

        def make_tab(parent, text, is_active, mode_target, col):
            bg_col = "#028090" if is_active else "#F1F5F9"
            fg_col = "#FFFFFF" if is_active else "#64748B"
            f = tk.Frame(parent, bg=bg_col, cursor="hand2")
            f.grid(row=0, column=col, sticky="nsew", padx=2)
            lbl = tk.Label(f, text=text, font=("Segoe UI", 9, "bold"), bg=bg_col, fg=fg_col, pady=5, cursor="hand2")
            lbl.pack(fill="both", expand=True)

            if not is_active:
                f.bind("<Enter>", lambda e, w=f, l=lbl: (w.config(bg="#E2E8F0"), l.config(bg="#E2E8F0")))
                lbl.bind("<Enter>", lambda e, w=f, l=lbl: (w.config(bg="#E2E8F0"), l.config(bg="#E2E8F0")))
                f.bind("<Leave>", lambda e, w=f, l=lbl: (w.config(bg="#F1F5F9"), l.config(bg="#F1F5F9")))
                lbl.bind("<Leave>", lambda e, w=f, l=lbl: (w.config(bg="#F1F5F9"), l.config(bg="#F1F5F9")))
                f.bind("<Button-1>", lambda e: self._set_mode(mode_target))
                lbl.bind("<Button-1>", lambda e: self._set_mode(mode_target))

        make_tab(tab_frame, "🔑  Sign In", is_login, "login", 0)
        make_tab(tab_frame, "📝  Register Account", not is_login, "register", 1)

        # 4. Error notification strip
        self.lbl_error = tk.Label(
            self.card,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#E63946"
        )
        self.lbl_error.pack(fill="x", pady=(0, 6))

        # 5. Data Entry Fields Container
        fields_frame = tk.Frame(self.card, bg="#FFFFFF")
        fields_frame.pack(fill="x", pady=(0, 6))

        if not is_login:
            self.entry_name = self._create_elegant_field(
                fields_frame, "Full Name", "👤", "Jane Cashier"
            )
            self.combo_role = self._create_elegant_field(
                fields_frame, "Role & Position", "💼", "Store Cashier",
                is_combobox=True,
                combo_values=["Store Cashier", "Inventory Manager", "Administrator"]
            )

        self.entry_email = self._create_elegant_field(
            fields_frame, "Work Email Address", "✉️",
            "admin@supermarket.com" if is_login else "cashier@supermarket.com"
        )

        self.entry_pass = self._create_elegant_field(
            fields_frame, "Password", "🔒",
            "admin123" if is_login else "pass123",
            is_password=True
        )

        # 6. Action Buttons Container
        btns_frame = tk.Frame(self.card, bg="#FFFFFF")
        btns_frame.pack(fill="x", pady=(6, 0))

        if is_login:
            # Login Button
            self.btn_login = ElegantButton(
                btns_frame,
                text="LOGIN TO CRUD OPERATIONS  →",
                command=self._execute_login,
                bg="#00B4D8",
                hover_bg="#0077B6",
                fg="#FFFFFF",
                font=("Segoe UI", 11, "bold"),
                pady=10
            )
            self.btn_login.pack(fill="x", pady=(0, 8))

            # Demo Login
            self.btn_demo = ElegantButton(
                btns_frame,
                text="⚡ Instant Demo Access (admin@supermarket.com)",
                command=self._execute_demo_login,
                bg="#E0F2FE",
                hover_bg="#BAE6FD",
                fg="#0369A1",
                font=("Segoe UI", 9, "bold"),
                pady=7
            )
            self.btn_demo.pack(fill="x")
        else:
            # Complete Registration Button
            self.btn_submit_reg = ElegantButton(
                btns_frame,
                text="COMPLETE REGISTRATION  ✓",
                command=self._execute_register,
                bg="#10B981",
                hover_bg="#059669",
                fg="#FFFFFF",
                font=("Segoe UI", 11, "bold"),
                pady=10
            )
            self.btn_submit_reg.pack(fill="x", pady=(0, 8))

            # Switch back to Login Button
            self.btn_back_login = ElegantButton(
                btns_frame,
                text="← Already have an account? Go to Login",
                command=lambda: self._set_mode("login"),
                bg="#F1F5F9",
                hover_bg="#E2E8F0",
                fg="#334155",
                font=("Segoe UI", 9, "bold"),
                pady=8,
                border_color="#CBD5E1"
            )
            self.btn_back_login.pack(fill="x")

        self.entry_email.focus_set()

    def _bind_hover(self, widget: tk.Button, normal_bg: str, hover_bg: str):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))

    def _toggle_password_visibility(self):
        self._show_pass = not self._show_pass
        if hasattr(self, "entry_pass"):
            self.entry_pass.config(show="" if self._show_pass else "•")
        if hasattr(self, "btn_eye") and self.btn_eye:
            self.btn_eye.config(text="🔒" if self._show_pass else "👁️", fg="#028090" if self._show_pass else "#64748B")

    def _set_mode(self, mode: str):
        self.current_mode = mode
        self._render_form_fields()

    def _on_enter_pressed(self):
        if not self.winfo_ismapped():
            return
        if self.current_mode == "login":
            self._execute_login()
        else:
            self._execute_register()

    def _execute_login(self):
        email = self.entry_email.get().strip().lower()
        password = self.entry_pass.get()

        ok, msg = validate_email(email)
        if not ok:
            self.lbl_error.config(text=f"⚠️ {msg}")
            self.entry_email.focus_set()
            return

        if not password:
            self.lbl_error.config(text="⚠️ Please enter your password.")
            self.entry_pass.focus_set()
            return

        if email in REGISTERED_USERS and REGISTERED_USERS[email]["password"] == password:
            user_info = REGISTERED_USERS[email].copy()
            user_info["email"] = email
            self.lbl_error.config(text="")
            if self.on_auth_success:
                self.on_auth_success(user_info)
        else:
            self.lbl_error.config(text="❌ Invalid credentials. Try demo login.")

    def _execute_demo_login(self):
        user_info = REGISTERED_USERS["admin@supermarket.com"].copy()
        user_info["email"] = "admin@supermarket.com"
        if self.on_auth_success:
            self.on_auth_success(user_info)

    def _execute_register(self):
        name = self.entry_name.get().strip()
        role = self.combo_role.get()
        email = self.entry_email.get().strip().lower()
        password = self.entry_pass.get()

        if not name:
            self.lbl_error.config(text="⚠️ Full Name cannot be empty.")
            self.entry_name.focus_set()
            return

        ok, msg = validate_email(email)
        if not ok:
            self.lbl_error.config(text=f"⚠️ {msg}")
            self.entry_email.focus_set()
            return

        if len(password) < 4:
            self.lbl_error.config(text="⚠️ Password must be at least 4 characters.")
            self.entry_pass.focus_set()
            return

        REGISTERED_USERS[email] = {"password": password, "name": name, "role": role}
        messagebox.showinfo("Registration Successful", f"Account created for {name} ({role})!\nNavigating to CRUD Operations Hub.")
        if self.on_auth_success:
            self.on_auth_success({"email": email, "name": name, "role": role})

    def _on_resize(self, event):
        if event.widget != self.canvas:
            return
        w, h = event.width, event.height
        if w < 10 or h < 10:
            return

        center_x = int(w * 0.50)
        self.canvas.coords("auth_title_main", center_x, 36)
        self.canvas.coords("auth_title_sub", center_x, 66)
        card_x = center_x
        card_y = max(int(h * 0.52), 370)
        self.canvas.coords(self.card_window, card_x, card_y)
        self.canvas.tag_raise(self.card_window)
        self.canvas.tag_raise("auth_title_main")
        self.canvas.tag_raise("auth_title_sub")

        # Avoid redundant PIL resizing on micro-movements
        if abs(w - self._last_bg_size[0]) < 15 and abs(h - self._last_bg_size[1]) < 15:
            return

        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass

        self._resize_job = self.after(50, lambda: self._perform_debounced_bg_resize(w, h))

    def _perform_debounced_bg_resize(self, w: int, h: int):
        self._resize_job = None
        self._last_bg_size = (w, h)
        self._draw_background(w, h)
