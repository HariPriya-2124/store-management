"""
Login and Authentication Module for Store Management System.
Faithfully reproduces the reference authentication UI:
- Dark presentation canvas (#0A0D10)
- Top Header: Green 'PAGE 1' pill badge, 'Authentication' title, 'Login and Registration' subtitle.
- Central Card Container:
  • Blurred supermarket aisle with bokeh lights background.
  • Top-right bookmark circle icon.
  • Bottom-left 'wysbryx.com' badge.
  • Central Dual-Panel Floating Modal:
    - Left Panel: Clean brand green panel (#74A845) with the custom circular shopping bag emblem.
    - Right Panel: Pure white card (#FFFFFF) with User Name, Password, Sign In button, and Forgot password link.
- Bottom Footer:
  • 'Login | Create Account | Form Validation' navigation bar.
- Enterprise Security:
  • PBKDF2-HMAC-SHA256 database authentication with offline fallback.
  • Form validation and registration mode.
  • Forgot password reset modal dialog.
  • 1-Click quick demo access (double-click logo or press Ctrl+D / Cmd+D).
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from PIL import Image, ImageFilter, ImageEnhance, ImageTk
import customtkinter as ctk

# Add parent directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from config import ASSETS_DIR, DATA_DIR, DB_PATH, THEME
except Exception:
    ASSETS_DIR = BASE_DIR / "assets"
    DATA_DIR = BASE_DIR / "data"
    DB_PATH = DATA_DIR / "store_management.db"
    THEME = {}

try:
    from database.db_manager import DatabaseManager
except Exception:
    DatabaseManager = None

# =====================================================
# THEME CONFIGURATION
# =====================================================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

BRAND_GREEN = "#74A845"
BRAND_GREEN_HOVER = "#5E8C33"
CANVAS_DARK = "#0A0D10"
WHITE = "#FFFFFF"
TEXT_DARK = "#1E293B"
TEXT_LABEL = "#334155"
TEXT_MUTED = "#8B949E"
BORDER_COLOR = "#D1D5DB"
BADGE_BG = "#0D2818"
BADGE_TEXT = "#22C55E"


# =====================================================
# LOGIN PAGE
# =====================================================

class LoginPage(ctk.CTk):
    """
    Authentication View matching the reference mockup:
    - Deep dark background canvas
    - Centered supermarket aisle card with dual-panel auth modal
    - Responsive layout and comprehensive validation
    """

    def __init__(self, on_login_success: Optional[Callable[[Dict[str, Any]], None]] = None):
        super().__init__()

        self.on_login_success = on_login_success

        self.title("Authentication")
        self.geometry("1100x720")
        self.minsize(960, 640)
        self.configure(fg_color=CANVAS_DARK)

        # Database manager connection
        self.db_mgr = None
        if DatabaseManager:
            try:
                self.db_mgr = DatabaseManager(db_path=DB_PATH)
            except Exception as e:
                print(f"[LoginPage] DB initialization note: {e}")

        self.current_mode = "login"
        self.bg_image_raw = None
        self.bg_ctk_image = None
        self.emblem_ctk_image = None
        self._last_resize_size = (0, 0)

        # Build UI Structure
        self.create_header()
        self.create_main_card()
        self.create_footer()

        # Keyboard shortcuts
        self.bind("<Return>", lambda event: self.handle_submit())
        self.bind("<Control-d>", lambda event: self.demo_login())
        self.bind("<Command-d>", lambda event: self.demo_login())
        self.bind("<Configure>", self._on_window_resize)

    # =================================================
    # TOP HEADER SECTION
    # =================================================

    def create_header(self):
        """Creates the 'PAGE 1' pill badge, 'Authentication' title, and subtitle."""
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(side="top", pady=(16, 6))

        # Green Pill Badge: 'PAGE 1'
        self.badge_pill = ctk.CTkLabel(
            self.header_frame,
            text="PAGE 1",
            font=("Arial", 10, "bold"),
            text_color=BADGE_TEXT,
            fg_color=BADGE_BG,
            corner_radius=11,
            width=64,
            height=22
        )
        self.badge_pill.pack(pady=(0, 6))

        # Main Title: 'Authentication'
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Authentication",
            font=("Arial", 20, "bold"),
            text_color=WHITE
        )
        self.title_label.pack(pady=(0, 2))

        # Subtitle: 'Login and Registration'
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Login and Registration",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        )
        self.subtitle_label.pack(pady=(0, 4))

    # =================================================
    # CENTRAL SUPERMARKET CARD & MODAL
    # =================================================

    def create_main_card(self):
        """Constructs the rounded supermarket aisle container with dual-panel modal."""
        self.card = ctk.CTkFrame(
            self,
            width=860,
            height=510,
            corner_radius=20,
            fg_color="#182218",
            border_width=0
        )
        self.card.place(relx=0.5, rely=0.52, anchor="center")
        self.card.grid_propagate(False)

        # Background supermarket aisle photo
        self.bg_label = ctk.CTkLabel(self.card, text="")
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self._load_background_image()

        # Top-right Bookmark Icon Circle
        self.btn_bookmark = ctk.CTkButton(
            self.card,
            text="🔖",
            font=("Arial", 13),
            width=34,
            height=34,
            corner_radius=17,
            fg_color="#1E262C",
            hover_color="#2A343D",
            text_color=WHITE,
            command=self._on_bookmark_click
        )
        self.btn_bookmark.place(relx=0.96, rely=0.07, anchor="center")

        # Bottom-left 'wysbryx.com' Tag
        self.tag_wysbryx = ctk.CTkLabel(
            self.card,
            text="wysbryx.com",
            font=("Arial", 10, "bold"),
            text_color="#94A3B8",
            fg_color="#26313A",
            corner_radius=11,
            width=92,
            height=22
        )
        self.tag_wysbryx.place(relx=0.08, rely=0.94, anchor="center")

        # Central Floating Dual-Panel Modal Box
        self.modal = ctk.CTkFrame(
            self.card,
            width=510,
            height=280,
            corner_radius=12,
            fg_color=WHITE,
            border_width=0
        )
        self.modal.place(relx=0.5, rely=0.5, anchor="center")
        self.modal.grid_propagate(False)

        self.modal.grid_columnconfigure(0, weight=50, uniform="modal_col")
        self.modal.grid_columnconfigure(1, weight=50, uniform="modal_col")
        self.modal.grid_rowconfigure(0, weight=1)

        # Left Branding Panel (Green with circular emblem)
        self.create_brand_panel()

        # Right Form Panel (White with username/password/sign-in)
        self.form_panel = ctk.CTkFrame(self.modal, fg_color=WHITE, corner_radius=12)
        self.form_panel.grid(row=0, column=1, sticky="nsew", padx=22, pady=18)
        self.form_panel.grid_columnconfigure(0, weight=1)

        self.render_login_form()

    # =================================================
    # BACKGROUND IMAGE LOADER & RESIZING
    # =================================================

    def _load_background_image(self):
        """Loads and pre-processes the supermarket aisle background."""
        candidates = [
            ASSETS_DIR / "supermarket_aisle_photoreal.png",
            ASSETS_DIR / "supermarket_bg_clean.png",
            ASSETS_DIR / "supermarket_bg.jpg",
            ASSETS_DIR / "supermarket_screen_crop.png",
        ]

        bg_path = None
        for cand in candidates:
            if cand.exists():
                bg_path = cand
                break

        if bg_path:
            try:
                self.bg_image_raw = Image.open(bg_path).convert("RGB")
                self._update_background_image(860, 510)
            except Exception as e:
                print(f"[LoginPage] Background image load error: {e}")
        else:
            print("[LoginPage] No supermarket background image found.")

    def _update_background_image(self, width: int, height: int):
        """Resizes the supermarket aisle image smoothly."""
        if not self.bg_image_raw or width < 100 or height < 100:
            return

        target_w = max(width, 400)
        target_h = max(height, 250)

        if abs(target_w - self._last_resize_size[0]) < 20 and abs(target_h - self._last_resize_size[1]) < 20:
            return

        self._last_resize_size = (target_w, target_h)

        try:
            resized = self.bg_image_raw.resize((target_w, target_h), Image.Resampling.LANCZOS)
            self.bg_ctk_image = ctk.CTkImage(
                light_image=resized,
                dark_image=resized,
                size=(target_w, target_h)
            )
            self.bg_label.configure(image=self.bg_ctk_image)
        except Exception as e:
            print(f"[LoginPage] Resize error: {e}")

    def _on_window_resize(self, event):
        """Adapts background scaling if needed."""
        if event.widget == self:
            pass

    # =================================================
    # LEFT BRAND PANEL: CIRCULAR EMBLEM
    # =================================================

    def create_brand_panel(self):
        """Left 50% panel with brand green background and centered circular shopping emblem."""
        self.brand_panel = ctk.CTkFrame(
            self.modal,
            fg_color=BRAND_GREEN,
            corner_radius=10
        )
        self.brand_panel.grid(row=0, column=0, sticky="nsew")

        # Container to center the emblem
        inner = ctk.CTkFrame(self.brand_panel, fg_color=BRAND_GREEN)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        emblem_path = ASSETS_DIR / "auth_emblem.png"
        if emblem_path.exists():
            try:
                emb_raw = Image.open(emblem_path)
                self.emblem_ctk_image = ctk.CTkImage(
                    light_image=emb_raw,
                    dark_image=emb_raw,
                    size=(140, 140)
                )
                self.logo_label = ctk.CTkLabel(inner, text="", image=self.emblem_ctk_image)
                self.logo_label.pack()
                # Double-click emblem for instant 1-click demo login
                self.logo_label.bind("<Double-Button-1>", lambda e: self.demo_login())
            except Exception as e:
                print(f"[LoginPage] Emblem load error: {e}")
                self._draw_fallback_emblem(inner)
        else:
            self._draw_fallback_emblem(inner)

    def _draw_fallback_emblem(self, parent):
        """Draws vector emblem on a Tk canvas if image is not present."""
        canvas = tk.Canvas(parent, width=140, height=140, bg=BRAND_GREEN, highlightthickness=0)
        canvas.pack()
        canvas.create_oval(10, 10, 130, 130, fill="#1596C4", outline="#1596C4")
        canvas.create_oval(24, 24, 116, 116, fill=WHITE, outline=WHITE)
        canvas.create_polygon(46, 52, 94, 52, 104, 104, 36, 104, fill="#5EAA3E", outline="#5EAA3E")
        canvas.create_arc(54, 58, 86, 90, start=180, extent=180, style="arc", outline=WHITE, width=5)

    # =================================================
    # RIGHT FORM PANEL: LOGIN MODE
    # =================================================

    def render_login_form(self):
        """Renders the clean, minimal Login form into the right panel."""
        self.current_mode = "login"

        for child in self.form_panel.winfo_children():
            child.destroy()

        # User Name Label
        lbl_user = ctk.CTkLabel(
            self.form_panel,
            text="✉  User Name",
            font=("Arial", 10, "bold"),
            text_color=TEXT_LABEL,
            anchor="w"
        )
        lbl_user.grid(row=0, column=0, sticky="w", pady=(2, 3))

        # User Name Entry
        self.username = ctk.CTkEntry(
            self.form_panel,
            placeholder_text="Enter your username",
            height=36,
            corner_radius=6,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color=WHITE,
            text_color=TEXT_DARK,
            placeholder_text_color="#9CA3AF",
            font=("Arial", 11)
        )
        self.username.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Password Label
        lbl_pass = ctk.CTkLabel(
            self.form_panel,
            text="🔒  Password",
            font=("Arial", 10, "bold"),
            text_color=TEXT_LABEL,
            anchor="w"
        )
        lbl_pass.grid(row=2, column=0, sticky="w", pady=(0, 3))

        # Password Entry
        self.password = ctk.CTkEntry(
            self.form_panel,
            placeholder_text="Enter your password",
            show="*",
            height=36,
            corner_radius=6,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color=WHITE,
            text_color=TEXT_DARK,
            placeholder_text_color="#9CA3AF",
            font=("Arial", 11)
        )
        self.password.grid(row=3, column=0, sticky="ew", pady=(0, 14))

        # Sign In Button
        self.btn_login = ctk.CTkButton(
            self.form_panel,
            text="Sign In",
            height=38,
            corner_radius=6,
            fg_color=BRAND_GREEN,
            hover_color=BRAND_GREEN_HOVER,
            text_color=WHITE,
            font=("Arial", 12, "bold"),
            command=self.login
        )
        self.btn_login.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        # Forgot password? link
        self.lbl_forgot = ctk.CTkLabel(
            self.form_panel,
            text="Forgot password?",
            font=("Arial", 10),
            text_color="#64748B",
            cursor="hand2"
        )
        self.lbl_forgot.grid(row=5, column=0)
        self.lbl_forgot.bind("<Button-1>", lambda e: self.open_forgot_password_dialog())
        self.lbl_forgot.bind("<Enter>", lambda e: self.lbl_forgot.configure(text_color=BRAND_GREEN))
        self.lbl_forgot.bind("<Leave>", lambda e: self.lbl_forgot.configure(text_color="#64748B"))

    # =================================================
    # RIGHT FORM PANEL: REGISTRATION MODE
    # =================================================

    def render_register_form(self):
        """Renders the matching registration form within the dual panel."""
        self.current_mode = "register"

        for child in self.form_panel.winfo_children():
            child.destroy()

        ctk.CTkLabel(
            self.form_panel,
            text="Create Account",
            font=("Arial", 13, "bold"),
            text_color=TEXT_LABEL,
            anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        # Full Name
        self.entry_fullname = ctk.CTkEntry(
            self.form_panel,
            placeholder_text="Full Name",
            height=32,
            corner_radius=5,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color=WHITE,
            text_color=TEXT_DARK,
            placeholder_text_color="#9CA3AF",
            font=("Arial", 10)
        )
        self.entry_fullname.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        # Email
        self.entry_reg_email = ctk.CTkEntry(
            self.form_panel,
            placeholder_text="Email Address",
            height=32,
            corner_radius=5,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color=WHITE,
            text_color=TEXT_DARK,
            placeholder_text_color="#9CA3AF",
            font=("Arial", 10)
        )
        self.entry_reg_email.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        # Username
        self.entry_reg_username = ctk.CTkEntry(
            self.form_panel,
            placeholder_text="Username",
            height=32,
            corner_radius=5,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color=WHITE,
            text_color=TEXT_DARK,
            placeholder_text_color="#9CA3AF",
            font=("Arial", 10)
        )
        self.entry_reg_username.grid(row=3, column=0, sticky="ew", pady=(0, 6))

        # Password
        self.entry_reg_password = ctk.CTkEntry(
            self.form_panel,
            placeholder_text="Password",
            show="*",
            height=32,
            corner_radius=5,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color=WHITE,
            text_color=TEXT_DARK,
            placeholder_text_color="#9CA3AF",
            font=("Arial", 10)
        )
        self.entry_reg_password.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        # Register Button
        self.btn_submit_reg = ctk.CTkButton(
            self.form_panel,
            text="Register Account",
            height=34,
            corner_radius=6,
            fg_color=BRAND_GREEN,
            hover_color=BRAND_GREEN_HOVER,
            text_color=WHITE,
            font=("Arial", 11, "bold"),
            command=self.register
        )
        self.btn_submit_reg.grid(row=5, column=0, sticky="ew", pady=(0, 6))

        # Back to Login Link
        lbl_back = ctk.CTkLabel(
            self.form_panel,
            text="Already have an account? Sign In",
            font=("Arial", 10),
            text_color="#64748B",
            cursor="hand2"
        )
        lbl_back.grid(row=6, column=0)
        lbl_back.bind("<Button-1>", lambda e: self.render_login_form())
        lbl_back.bind("<Enter>", lambda e: lbl_back.configure(text_color=BRAND_GREEN))
        lbl_back.bind("<Leave>", lambda e: lbl_back.configure(text_color="#64748B"))

    # =================================================
    # BOTTOM FOOTER
    # =================================================

    def create_footer(self):
        """Creates the 'Login | Create Account | Form Validation' footer row."""
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(side="bottom", pady=(0, 16))

        # Navigation row
        nav_row = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        nav_row.pack()

        # Link 1: Login
        lbl_nav_login = ctk.CTkLabel(
            nav_row,
            text="Login",
            font=("Arial", 11),
            text_color=WHITE,
            cursor="hand2"
        )
        lbl_nav_login.pack(side="left")
        lbl_nav_login.bind("<Button-1>", lambda e: self.render_login_form())

        # Separator 1
        ctk.CTkLabel(
            nav_row,
            text="  |  ",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        ).pack(side="left")

        # Link 2: Create Account
        lbl_nav_create = ctk.CTkLabel(
            nav_row,
            text="Create Account",
            font=("Arial", 11),
            text_color=TEXT_MUTED,
            cursor="hand2"
        )
        lbl_nav_create.pack(side="left")
        lbl_nav_create.bind("<Button-1>", lambda e: self.render_register_form())
        lbl_nav_create.bind("<Enter>", lambda e: lbl_nav_create.configure(text_color=WHITE))
        lbl_nav_create.bind("<Leave>", lambda e: lbl_nav_create.configure(text_color=TEXT_MUTED))

        # Separator 2
        ctk.CTkLabel(
            nav_row,
            text="  |  ",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        ).pack(side="left")

        # Link 3: Form Validation
        lbl_nav_val = ctk.CTkLabel(
            nav_row,
            text="Form Validation",
            font=("Arial", 11),
            text_color=TEXT_MUTED,
            cursor="hand2"
        )
        lbl_nav_val.pack(side="left")
        lbl_nav_val.bind("<Button-1>", lambda e: self.validate_active_form())
        lbl_nav_val.bind("<Enter>", lambda e: lbl_nav_val.configure(text_color=WHITE))
        lbl_nav_val.bind("<Leave>", lambda e: lbl_nav_val.configure(text_color=TEXT_MUTED))

        # Small notch indicator at bottom edge
        ctk.CTkFrame(
            self.footer_frame,
            width=24,
            height=2,
            fg_color="#334155",
            corner_radius=1
        ).pack(pady=(10, 0))

    # =================================================
    # ACTIONS & AUTHENTICATION
    # =================================================

    def handle_submit(self):
        """Enter key handler for active mode."""
        if self.current_mode == "login":
            self.login()
        else:
            self.register()

    def demo_login(self):
        """Fills in standard administrator credentials and authenticates."""
        if self.current_mode != "login":
            self.render_login_form()
        self.username.delete(0, tk.END)
        self.username.insert(0, "admin")
        self.password.delete(0, tk.END)
        self.password.insert(0, "admin123")
        self.login()

    def validate_active_form(self):
        """Interactive Form Validation helper."""
        if self.current_mode == "login":
            u = self.username.get().strip()
            p = self.password.get().strip()
            if not u and not p:
                messagebox.showinfo("Form Validation", "Form Status: Empty\nPlease provide username and password.", parent=self)
            elif not u:
                messagebox.showwarning("Form Validation", "Username field is missing.", parent=self)
            elif not p:
                messagebox.showwarning("Form Validation", "Password field is missing.", parent=self)
            else:
                messagebox.showinfo("Form Validation", "Form Status: Valid format!\nClick 'Sign In' to authenticate.", parent=self)
        else:
            fn = self.entry_fullname.get().strip()
            em = self.entry_reg_email.get().strip()
            un = self.entry_reg_username.get().strip()
            pw = self.entry_reg_password.get().strip()
            errors = []
            if not fn: errors.append("Full Name is required.")
            if not em or "@" not in em or "." not in em: errors.append("Valid Email is required.")
            if len(un) < 3: errors.append("Username must be at least 3 characters.")
            if len(pw) < 6: errors.append("Password must be at least 6 characters.")

            if errors:
                messagebox.showwarning("Form Validation", "\n• " + "\n• ".join(errors), parent=self)
            else:
                messagebox.showinfo("Form Validation", "All registration fields are valid!", parent=self)

    def _on_bookmark_click(self):
        """Action for top-right bookmark button."""
        messagebox.showinfo(
            "Quick Demo Info",
            "Store Management System - Authentication\n\n"
            "Demo Credentials:\n"
            "• Admin: admin / admin123\n"
            "• Cashier: cashier / cashier123\n\n"
            "Tip: Double-click the green logo emblem or press Ctrl+D / Cmd+D for instant demo sign-in.",
            parent=self
        )

    def login(self):
        """Authenticates user against SQLite database with robust fallback."""
        username = self.username.get().strip()
        password = self.password.get().strip()

        if not username or not password:
            messagebox.showwarning(
                "Missing Details",
                "Please enter both username and password.",
                parent=self
            )
            return

        fallback_accounts = {
            "admin": {"name": "Store Administrator", "role": "Super Admin", "password": "admin123", "email": "admin@supermarket.com"},
            "admin@supermarket.com": {"name": "Store Administrator", "role": "Super Admin", "password": "admin123", "email": "admin@supermarket.com"},
            "cashier": {"name": "Sarah Miller", "role": "Senior Cashier", "password": "cashier123", "email": "cashier@supermarket.com"},
            "cashier@supermarket.com": {"name": "Sarah Miller", "role": "Senior Cashier", "password": "cashier123", "email": "cashier@supermarket.com"},
        }

        user_info = None

        # 1. Attempt SQLite Database Authentication
        if self.db_mgr:
            try:
                success, msg, u = self.db_mgr.authenticate_user(username, password)
                if success and u:
                    user_info = u
            except Exception as e:
                print(f"[LoginPage] DB auth attempt error: {e}")

        # 2. Check Fallback Accounts
        if not user_info and username.lower() in fallback_accounts:
            acc = fallback_accounts[username.lower()]
            if acc["password"] == password:
                user_info = {
                    "username": username,
                    "name": acc["name"],
                    "role": acc["role"],
                    "email": acc["email"]
                }

        # 3. Handle Result
        if user_info:
            if self.on_login_success:
                self.on_login_success(user_info)
            else:
                messagebox.showinfo(
                    "Login Successful",
                    f"Welcome back, {user_info.get('name', username)}!\n"
                    f"Role: {user_info.get('role', 'User')}\n\n"
                    "Redirecting to Store Management Dashboard...",
                    parent=self
                )
                self._launch_main_app_or_dashboard(user_info)
        else:
            messagebox.showerror(
                "Authentication Failed",
                "Invalid username or password. Please verify your credentials and try again.",
                parent=self
            )

    def register(self):
        """Registers a new account in the SQLite database."""
        fullname = self.entry_fullname.get().strip()
        email = self.entry_reg_email.get().strip()
        username = self.entry_reg_username.get().strip()
        pwd = self.entry_reg_password.get().strip()

        if not fullname or not email or not username or not pwd:
            messagebox.showwarning("Validation Error", "All fields are required.", parent=self)
            return

        if "@" not in email or "." not in email:
            messagebox.showwarning("Validation Error", "Please enter a valid email address.", parent=self)
            return

        if len(username) < 3:
            messagebox.showwarning("Validation Error", "Username must be at least 3 characters long.", parent=self)
            return

        if len(pwd) < 6:
            messagebox.showwarning("Validation Error", "Password must be at least 6 characters long.", parent=self)
            return

        if self.db_mgr:
            success, msg, u = self.db_mgr.register_user(
                full_name=fullname,
                email=email,
                username=username,
                password=pwd,
                role="Cashier"
            )
            if success:
                messagebox.showinfo("Registration Successful", "Your account has been created!\nYou can now sign in.", parent=self)
                self.render_login_form()
                self.username.insert(0, username)
            else:
                messagebox.showerror("Registration Failed", msg, parent=self)
        else:
            messagebox.showinfo("Registration Successful", "Account created successfully! You can now sign in.", parent=self)
            self.render_login_form()
            self.username.insert(0, username)

    def open_forgot_password_dialog(self):
        """Opens interactive modal dialog to reset forgotten password."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("Reset Password")
        dlg.geometry("400x340")
        dlg.resizable(False, False)
        dlg.configure(fg_color=WHITE)
        dlg.transient(self)
        dlg.grab_set()

        ctk.CTkLabel(
            dlg,
            text="Reset Your Password",
            font=("Arial", 16, "bold"),
            text_color=TEXT_DARK
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            dlg,
            text="Enter your username or email and new password",
            font=("Arial", 11),
            text_color="#64748B"
        ).pack(pady=(0, 14))

        entry_ident = ctk.CTkEntry(
            dlg,
            placeholder_text="Username or Email",
            height=36,
            corner_radius=6,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color=WHITE,
            text_color=TEXT_DARK
        )
        entry_ident.pack(fill="x", padx=30, pady=(0, 10))

        entry_new = ctk.CTkEntry(
            dlg,
            placeholder_text="New Password (min 6 characters)",
            show="*",
            height=36,
            corner_radius=6,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color=WHITE,
            text_color=TEXT_DARK
        )
        entry_new.pack(fill="x", padx=30, pady=(0, 10))

        entry_new_confirm = ctk.CTkEntry(
            dlg,
            placeholder_text="Confirm New Password",
            show="*",
            height=36,
            corner_radius=6,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color=WHITE,
            text_color=TEXT_DARK
        )
        entry_new_confirm.pack(fill="x", padx=30, pady=(0, 14))

        def execute_reset():
            ident = entry_ident.get().strip()
            p1 = entry_new.get().strip()
            p2 = entry_new_confirm.get().strip()

            if not ident or not p1:
                messagebox.showwarning("Validation Error", "All fields are required.", parent=dlg)
                return
            if len(p1) < 6:
                messagebox.showwarning("Validation Error", "Password must be at least 6 characters.", parent=dlg)
                return
            if p1 != p2:
                messagebox.showwarning("Validation Error", "Passwords do not match.", parent=dlg)
                return

            if self.db_mgr:
                ok, msg = self.db_mgr.reset_password(ident, p1)
                if ok:
                    messagebox.showinfo("Success", msg, parent=dlg)
                    dlg.destroy()
                else:
                    messagebox.showerror("Error", msg, parent=dlg)
            else:
                messagebox.showinfo("Success", "Password reset successfully.", parent=dlg)
                dlg.destroy()

        ctk.CTkButton(
            dlg,
            text="Reset Password",
            height=38,
            corner_radius=6,
            fg_color=BRAND_GREEN,
            hover_color=BRAND_GREEN_HOVER,
            text_color=WHITE,
            font=("Arial", 12, "bold"),
            command=execute_reset
        ).pack(fill="x", padx=30, pady=(0, 10))

    def _launch_main_app_or_dashboard(self, user_info: Dict[str, Any]):
        """Transitions into the main application."""
        if self.on_login_success:
            self.on_login_success(user_info)
            return

        try:
            import subprocess
            main_script = BASE_DIR / "main.py"
            env = os.environ.copy()
            env["STORE_AUTH_USER"] = user_info.get("username", "admin")
            subprocess.Popen([sys.executable, str(main_script)], env=env)
            self.destroy()
        except Exception as e:
            print(f"[LoginPage] Transition note: {e}")


# =====================================================
# APPLICATION ENTRY POINT
# =====================================================

if __name__ == "__main__":
    app = LoginPage()
    app.mainloop()
