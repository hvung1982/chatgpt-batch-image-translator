import os
import sys
import csv
import json
import queue
import shutil
import threading
import subprocess
import ctypes
import signal
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path


THEME_LABELS = {
    "system": "Hệ thống",
    "light": "Sáng",
    "dark": "Tối",
}

THEME_VALUES = {label: value for value, label in THEME_LABELS.items()}

THEMES = {
    "light": {
        "window": "#eef0f4",
        "chrome": "#f7f7fa",
        "sidebar": "#e8ebf0",
        "surface": "#ffffff",
        "surface_alt": "#fbfcfe",
        "surface_hover": "#f2f4f7",
        "text": "#111827",
        "muted": "#667085",
        "field_text": "#344054",
        "border": "#d0d5dd",
        "progress_trough": "#e4e7ec",
        "log_bg": "#f8fafc",
        "log_text": "#182230",
        "selection_bg": "#c7ddff",
        "selection_text": "#111827",
        "blue": "#0a84ff",
        "blue_active": "#006edb",
        "blue_disabled": "#93c5fd",
        "purple": "#5856d6",
        "purple_active": "#4745b8",
        "purple_disabled": "#c4b5fd",
        "green": "#34c759",
        "green_active": "#248a3d",
        "green_disabled": "#a6e7b7",
        "red": "#ff3b30",
        "red_active": "#d92d20",
    },
    "dark": {
        "window": "#15171c",
        "chrome": "#1d2027",
        "sidebar": "#20242c",
        "surface": "#252932",
        "surface_alt": "#1f232b",
        "surface_hover": "#303540",
        "text": "#f4f7fb",
        "muted": "#aab3c2",
        "field_text": "#d8dee8",
        "border": "#3f4654",
        "progress_trough": "#333946",
        "log_bg": "#171a20",
        "log_text": "#e6ebf2",
        "selection_bg": "#265fbd",
        "selection_text": "#ffffff",
        "blue": "#0a84ff",
        "blue_active": "#3b9cff",
        "blue_disabled": "#305f91",
        "purple": "#7c79ff",
        "purple_active": "#9391ff",
        "purple_disabled": "#55518a",
        "green": "#30d158",
        "green_active": "#58df78",
        "green_disabled": "#3c7a4d",
        "red": "#ff453a",
        "red_active": "#ff6961",
    },
}


def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()
SCRIPT_FILE = APP_DIR / "run_chatgpt_batch.py"
APP_NAME = "ChatGPT Batch Translator"


def is_macos():
    return sys.platform == "darwin"


def get_user_data_dir():
    if is_macos():
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return APP_DIR


USER_DATA_DIR = get_user_data_dir()
SETTINGS_FILE = USER_DATA_DIR / "app_settings.json"

DEFAULT_SETTINGS = {
    "image_folder": str((USER_DATA_DIR if is_macos() else APP_DIR) / "images"),
    "download_folder": str((USER_DATA_DIR if is_macos() else APP_DIR) / "images_vn"),
    "profile_dir": str(USER_DATA_DIR / "chatgpt_auto_profile"),
    "batch_size": "5",
    "start_from": "",
    "theme": "system"
}


def enable_windows_dpi_awareness():
    if os.name != "nt":
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def get_windows_system_theme():
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value else "dark"
    except Exception:
        return "light"


def get_macos_system_theme():
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1,
            check=False,
        )
        return "dark" if "dark" in result.stdout.lower() else "light"
    except Exception:
        return "light"


def get_system_theme():
    if is_macos():
        return get_macos_system_theme()
    if os.name == "nt":
        return get_windows_system_theme()
    return "light"


def run_packaged_worker():
    import run_chatgpt_batch

    run_chatgpt_batch.main()


class ChatGPTBatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ChatGPT Batch Translator PRO")
        self.root.geometry("1280x840")
        self.root.minsize(1120, 720)

        self.proc = None
        self.log_queue = queue.Queue()
        self.current_done = 0
        self.current_total = 0

        self.settings = self.load_settings()
        self.theme_mode = self.normalize_theme(self.settings.get("theme"))
        self.current_theme = None
        self.tk_theme_widgets = []
        self.log_text = None
        self.log_scrollbar = None
        self.theme_var = tk.StringVar(value=THEME_LABELS[self.theme_mode])

        self.setup_style()
        self.build_ui()
        self.watch_system_theme()
        self.poll_log_queue()

    def setup_style(self):
        self.ui_font = ".AppleSystemUIFont" if is_macos() else "Segoe UI"
        self.mono_font = "Menlo" if is_macos() else "Cascadia Mono"

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.apply_theme_styles()

    def normalize_theme(self, value):
        return value if value in THEME_LABELS else "system"

    def resolve_theme(self):
        return get_system_theme() if self.theme_mode == "system" else self.theme_mode

    def palette(self):
        return THEMES[self.resolve_theme()]

    def apply_theme_styles(self):
        palette = self.palette()
        self.current_theme = self.resolve_theme()
        self.root.configure(bg=palette["window"])

        self.style.configure("TFrame", background=palette["window"])
        self.style.configure("App.TFrame", background=palette["window"])
        self.style.configure("Chrome.TFrame", background=palette["chrome"])
        self.style.configure("Sidebar.TFrame", background=palette["sidebar"])
        self.style.configure("Main.TFrame", background=palette["window"])
        self.style.configure("Card.TFrame", background=palette["surface"], relief="flat")
        self.style.configure("Toolbar.TFrame", background=palette["surface"], relief="flat")

        self.style.configure(
            "Title.TLabel",
            background=palette["window"],
            foreground=palette["text"],
            font=(self.ui_font, 17, "bold")
        )

        self.style.configure(
            "Sub.TLabel",
            background=palette["window"],
            foreground=palette["muted"],
            font=(self.ui_font, 9)
        )

        self.style.configure(
            "ChromeTitle.TLabel",
            background=palette["chrome"],
            foreground=palette["text"],
            font=(self.ui_font, 10, "bold")
        )

        self.style.configure(
            "SidebarTitle.TLabel",
            background=palette["sidebar"],
            foreground=palette["text"],
            font=(self.ui_font, 14, "bold")
        )

        self.style.configure(
            "SidebarSub.TLabel",
            background=palette["sidebar"],
            foreground=palette["muted"],
            font=(self.ui_font, 9)
        )

        self.style.configure(
            "SectionTitle.TLabel",
            background=palette["surface"],
            foreground=palette["text"],
            font=(self.ui_font, 10, "bold")
        )

        self.style.configure(
            "SectionHint.TLabel",
            background=palette["surface"],
            foreground=palette["muted"],
            font=(self.ui_font, 9)
        )

        self.style.configure(
            "Field.TLabel",
            background=palette["surface"],
            foreground=palette["field_text"],
            font=(self.ui_font, 9)
        )

        self.style.configure(
            "TLabel",
            background=palette["surface"],
            foreground=palette["text"],
            font=(self.ui_font, 10)
        )

        self.style.configure(
            "TEntry",
            fieldbackground=palette["surface_alt"],
            background=palette["surface_alt"],
            foreground=palette["text"],
            bordercolor=palette["border"],
            lightcolor=palette["border"],
            darkcolor=palette["border"],
            insertcolor=palette["text"],
            font=(self.ui_font, 10),
            padding=8
        )

        self.style.map(
            "TEntry",
            fieldbackground=[("disabled", palette["surface_hover"]), ("readonly", palette["surface_alt"])],
            foreground=[("disabled", palette["muted"])],
        )

        self.style.configure(
            "Theme.TCombobox",
            fieldbackground=palette["surface_alt"],
            background=palette["surface_alt"],
            foreground=palette["text"],
            bordercolor=palette["border"],
            arrowcolor=palette["muted"],
            selectbackground=palette["surface_alt"],
            selectforeground=palette["text"],
            padding=5,
        )

        self.style.map(
            "Theme.TCombobox",
            fieldbackground=[("readonly", palette["surface_alt"])],
            foreground=[("readonly", palette["text"])],
            selectbackground=[("readonly", palette["surface_alt"])],
            selectforeground=[("readonly", palette["text"])],
        )

        self.style.configure(
            "Blue.TButton",
            background=palette["blue"],
            foreground="white",
            font=(self.ui_font, 10, "bold"),
            padding=(14, 8),
            borderwidth=0
        )

        self.style.map("Blue.TButton", background=[("active", palette["blue_active"]), ("disabled", palette["blue_disabled"])])

        self.style.configure(
            "Purple.TButton",
            background=palette["purple"],
            foreground="white",
            font=(self.ui_font, 10, "bold"),
            padding=(14, 8),
            borderwidth=0
        )

        self.style.map("Purple.TButton", background=[("active", palette["purple_active"]), ("disabled", palette["purple_disabled"])])

        self.style.configure(
            "Green.TButton",
            background=palette["green"],
            foreground="white",
            font=(self.ui_font, 10, "bold"),
            padding=(14, 8),
            borderwidth=0
        )

        self.style.map("Green.TButton", background=[("active", palette["green_active"]), ("disabled", palette["green_disabled"])])

        self.style.configure(
            "Red.TButton",
            background=palette["red"],
            foreground="white",
            font=(self.ui_font, 10, "bold"),
            padding=(14, 8),
            borderwidth=0
        )

        self.style.map("Red.TButton", background=[("active", palette["red_active"])])

        self.style.configure(
            "Gray.TButton",
            background=palette["surface_hover"],
            foreground=palette["text"],
            font=(self.ui_font, 10),
            padding=(12, 8),
            borderwidth=0
        )

        self.style.map("Gray.TButton", background=[("active", palette["border"])])

        self.style.configure(
            "Ghost.TButton",
            background=palette["surface"],
            foreground=palette["field_text"],
            font=(self.ui_font, 10),
            padding=(12, 8),
            borderwidth=0
        )

        self.style.map("Ghost.TButton", background=[("active", palette["surface_hover"])])

        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor=palette["progress_trough"],
            background=palette["blue"],
            thickness=10,
            bordercolor=palette["progress_trough"],
            lightcolor=palette["blue"],
            darkcolor=palette["blue"]
        )

        self.style.configure(
            "Log.Vertical.TScrollbar",
            background=palette["surface_hover"],
            troughcolor=palette["log_bg"],
            bordercolor=palette["log_bg"],
            arrowcolor=palette["muted"],
            lightcolor=palette["surface_hover"],
            darkcolor=palette["surface_hover"],
        )
        self.style.map(
            "Log.Vertical.TScrollbar",
            background=[("active", palette["border"])],
            arrowcolor=[("active", palette["text"])],
        )

        for widget, role in self.tk_theme_widgets:
            self.apply_tk_theme(widget, role)

        if self.log_text is not None:
            self.log_text.configure(
                bg=palette["log_bg"],
                fg=palette["log_text"],
                insertbackground=palette["text"],
                selectbackground=palette["selection_bg"],
                selectforeground=palette["selection_text"],
            )
            self.apply_log_scrollbar_theme()

    def apply_log_scrollbar_theme(self):
        palette = self.palette()
        if self.log_scrollbar is None:
            return

        try:
            self.log_scrollbar.configure(style="Log.Vertical.TScrollbar")
        except tk.TclError:
            pass

    def apply_tk_theme(self, widget, role):
        palette = self.palette()
        backgrounds = {
            "chrome": palette["chrome"],
            "sidebar": palette["sidebar"],
            "surface": palette["surface"],
        }
        foregrounds = {
            "muted": palette["muted"],
            "text": palette["text"],
        }
        options = {}
        if role in backgrounds:
            options["bg"] = backgrounds[role]
        elif role in foregrounds:
            options["fg"] = foregrounds[role]
        if options:
            try:
                widget.configure(**options)
            except tk.TclError:
                pass

    def register_tk_theme(self, widget, role):
        self.tk_theme_widgets.append((widget, role))
        self.apply_tk_theme(widget, role)
        return widget

    def themed_frame(self, parent, role, **kwargs):
        frame = tk.Frame(parent, **kwargs)
        return self.register_tk_theme(frame, role)

    def themed_label(self, parent, bg_role, fg_role, **kwargs):
        label = tk.Label(parent, **kwargs)
        self.register_tk_theme(label, bg_role)
        self.register_tk_theme(label, fg_role)
        return label

    def on_theme_changed(self, _event=None):
        self.theme_mode = THEME_VALUES.get(self.theme_var.get(), "system")
        self.apply_theme_styles()
        self.save_settings()

    def watch_system_theme(self):
        if self.theme_mode == "system":
            resolved = self.resolve_theme()
            if resolved != self.current_theme:
                self.apply_theme_styles()
        self.root.after(3000, self.watch_system_theme)

    def load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return {**DEFAULT_SETTINGS, **json.load(f)}
            except Exception:
                pass

        return DEFAULT_SETTINGS.copy()

    def save_settings(self):
        data = {
            "image_folder": self.image_var.get(),
            "download_folder": self.output_var.get(),
            "profile_dir": self.profile_var.get(),
            "batch_size": self.batch_var.get(),
            "start_from": self.start_from_var.get(),
            "theme": self.theme_mode
        }

        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def build_ui(self):
        outer = ttk.Frame(self.root, style="App.TFrame")
        outer.pack(fill="both", expand=True)

        chrome = ttk.Frame(outer, style="Chrome.TFrame", padding=(18, 9))
        chrome.pack(fill="x")

        dots = self.themed_frame(chrome, "chrome")
        dots.pack(side="left", padx=(0, 14))
        for color in ("#ff5f57", "#febc2e", "#28c840"):
            dot = tk.Label(
                dots,
                text="●",
                fg=color,
                font=(self.ui_font, 11),
            )
            self.register_tk_theme(dot, "chrome")
            dot.pack(side="left", padx=2)

        ttk.Label(
            chrome,
            text="ChatGPT Batch Translator PRO",
            style="ChromeTitle.TLabel"
        ).pack(side="left")

        theme_picker = ttk.Combobox(
            chrome,
            textvariable=self.theme_var,
            values=list(THEME_VALUES.keys()),
            state="readonly",
            width=10,
            style="Theme.TCombobox",
        )
        theme_picker.pack(side="right")
        theme_picker.bind("<<ComboboxSelected>>", self.on_theme_changed)
        ttk.Label(chrome, text="Giao diện", style="ChromeTitle.TLabel").pack(side="right", padx=(0, 8))

        body = ttk.Frame(outer, style="App.TFrame", padding=(12, 12, 12, 12))
        body.pack(fill="both", expand=True)

        sidebar = ttk.Frame(body, style="Sidebar.TFrame", padding=(16, 16))
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)
        sidebar.configure(width=320)

        ttk.Label(
            sidebar,
            text="Dịch sách tự động",
            style="SidebarTitle.TLabel",
            wraplength=280
        ).pack(anchor="w")
        ttk.Label(
            sidebar,
            text="Upload ảnh, dịch nội dung, tạo ảnh Việt hóa và quản lý batch.",
            style="SidebarSub.TLabel",
            wraplength=280,
            justify="left"
        ).pack(anchor="w", pady=(6, 16))

        self.status_var = tk.StringVar(value="Sẵn sàng")
        status_box = self.themed_frame(sidebar, "surface", padx=12, pady=12)
        status_box.pack(fill="x", pady=(0, 14))
        self.themed_label(
            status_box,
            "surface",
            "muted",
            text="Trạng thái",
            font=(self.ui_font, 9, "bold")
        ).pack(anchor="w")
        self.themed_label(
            status_box,
            "surface",
            "text",
            textvariable=self.status_var,
            font=(self.ui_font, 10, "bold"),
            wraplength=260,
            justify="left"
        ).pack(anchor="w", pady=(6, 0))

        self.progress_var = tk.DoubleVar(value=0)
        progress_box = self.themed_frame(sidebar, "surface", padx=12, pady=12)
        progress_box.pack(fill="x", pady=(0, 14))
        self.themed_label(
            progress_box,
            "surface",
            "muted",
            text="Tiến trình",
            font=(self.ui_font, 9, "bold")
        ).pack(anchor="w")
        ttk.Progressbar(
            progress_box,
            variable=self.progress_var,
            maximum=100,
            style="Horizontal.TProgressbar"
        ).pack(fill="x", pady=(8, 5))

        self.progress_label = tk.StringVar(value="Tiến trình: 0%")
        self.themed_label(
            progress_box,
            "surface",
            "muted",
            textvariable=self.progress_label,
            font=(self.ui_font, 9),
            wraplength=260,
            justify="left"
        ).pack(anchor="w")

        ttk.Label(sidebar, text="Thao tác nhanh", style="SidebarSub.TLabel").pack(anchor="w", pady=(8, 8))
        ttk.Button(sidebar, text="Mở kết quả", command=self.open_output, style="Ghost.TButton").pack(fill="x", pady=3)
        ttk.Button(sidebar, text="Xuất lỗi", command=self.export_failed, style="Ghost.TButton").pack(fill="x", pady=3)
        ttk.Button(sidebar, text="Copy lỗi", command=self.copy_failed_retry, style="Ghost.TButton").pack(fill="x", pady=3)
        ttk.Button(sidebar, text="Lưu cấu hình", command=self.save_and_notify, style="Ghost.TButton").pack(fill="x", pady=3)
        ttk.Button(sidebar, text="Xóa log", command=self.clear_log, style="Ghost.TButton").pack(fill="x", pady=3)

        main = ttk.Frame(body, style="Main.TFrame")
        main.pack(side="left", fill="both", expand=True)

        header = ttk.Frame(main, style="Main.TFrame")
        header.pack(fill="x", pady=(0, 6))

        ttk.Label(header, text="Bảng điều khiển", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Chạy batch ổn định, theo dõi tiến trình và can thiệp thủ công khi ChatGPT yêu cầu.",
            style="Sub.TLabel"
        ).pack(anchor="w", pady=(2, 0))

        self.image_var = tk.StringVar(value=self.settings["image_folder"])
        self.output_var = tk.StringVar(value=self.settings["download_folder"])
        self.profile_var = tk.StringVar(value=self.settings["profile_dir"])
        self.batch_var = tk.StringVar(value=self.settings["batch_size"])
        self.start_from_var = tk.StringVar(value=self.settings.get("start_from", ""))

        config_card = ttk.Frame(main, style="Card.TFrame", padding=(14, 8))
        config_card.pack(fill="x", pady=(0, 6))

        ttk.Label(config_card, text="Cấu hình nguồn dữ liệu", style="SectionTitle.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 2)
        )
        ttk.Label(
            config_card,
            text="Giữ profile ChatGPT riêng để hạn chế đăng nhập lại và không đưa thư mục này lên GitHub.",
            style="SectionHint.TLabel"
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 6))

        self.add_folder_row(config_card, "Thư mục ảnh gốc", self.image_var, 2)
        self.add_folder_row(config_card, "Thư mục lưu ảnh VN", self.output_var, 3)
        self.add_folder_row(config_card, "Profile ChatGPT", self.profile_var, 4)

        ttk.Label(config_card, text="Số ảnh mỗi lần", style="Field.TLabel").grid(
            row=5, column=0, sticky="w", padx=(0, 12), pady=(5, 3)
        )
        ttk.Entry(config_card, textvariable=self.batch_var, width=12).grid(row=5, column=1, sticky="w", pady=(5, 3))

        ttk.Label(config_card, text="Bắt đầu từ ảnh", style="Field.TLabel").grid(
            row=6, column=0, sticky="w", padx=(0, 12), pady=3
        )
        ttk.Entry(config_card, textvariable=self.start_from_var, width=24).grid(row=6, column=1, sticky="w", pady=3)

        ttk.Label(
            config_card,
            text="Ví dụ: 66, 122, 66_122 hoặc 66_122.jpg",
            style="SectionHint.TLabel"
        ).grid(row=7, column=1, sticky="w", pady=(0, 3))

        config_card.columnconfigure(1, weight=1)

        action_card = ttk.Frame(main, style="Toolbar.TFrame", padding=(14, 7))
        action_card.pack(fill="x", pady=(0, 6))

        self.start_btn = ttk.Button(
            action_card,
            text="Chạy batch mới",
            command=lambda: self.start("main"),
            style="Blue.TButton"
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.retry_btn = ttk.Button(
            action_card,
            text="Chạy lại ảnh lỗi",
            command=lambda: self.start("retry"),
            style="Purple.TButton"
        )
        self.retry_btn.pack(side="left", padx=8)

        self.force_btn = ttk.Button(
            action_card,
            text="Chạy lại ảnh này",
            command=lambda: self.start("force"),
            style="Gray.TButton"
        )
        self.force_btn.pack(side="left", padx=8)

        self.continue_btn = ttk.Button(
            action_card,
            text="Tiếp tục sau can thiệp",
            command=self.send_continue,
            style="Green.TButton",
            state="disabled"
        )
        self.continue_btn.pack(side="left", padx=8)

        self.stop_btn = ttk.Button(
            action_card,
            text="Dừng",
            command=self.stop,
            style="Red.TButton"
        )
        self.stop_btn.pack(side="left", padx=8)

        log_card = ttk.Frame(main, style="Card.TFrame", padding=(14, 10))
        log_card.pack(fill="both", expand=True)

        ttk.Label(
            log_card,
            text="Nhật ký xử lý",
            style="SectionTitle.TLabel"
        ).pack(anchor="w", pady=(0, 5))

        log_frame = ttk.Frame(log_card, style="Card.TFrame")
        log_frame.pack(fill="both", expand=True)

        palette = self.palette()
        self.log_text = tk.Text(
            log_frame,
            wrap="word",
            font=(self.mono_font, 10),
            bg=palette["log_bg"],
            fg=palette["log_text"],
            insertbackground=palette["text"],
            selectbackground=palette["selection_bg"],
            selectforeground=palette["selection_text"],
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=12,
            height=20
        )
        self.log_scrollbar = ttk.Scrollbar(
            log_frame,
            orient="vertical",
            command=self.log_text.yview,
            style="Log.Vertical.TScrollbar",
        )
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_scrollbar.pack(side="right", fill="y")
        self.apply_theme_styles()

    def add_folder_row(self, parent, label, var, row):
        ttk.Label(parent, text=label, style="Field.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=3)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Button(
            parent,
            text="Chọn",
            command=lambda: self.choose_folder(var),
            style="Gray.TButton"
        ).grid(row=row, column=2, padx=(10, 0), pady=3)

    def choose_folder(self, var):
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)

    def save_and_notify(self):
        self.save_settings()
        messagebox.showinfo("OK", "Đã lưu cấu hình.")

    def start(self, mode):
        if self.proc and self.proc.poll() is None:
            messagebox.showwarning("Đang chạy", "Batch đang chạy.")
            return

        if mode == "force" and not self.start_from_var.get().strip():
            messagebox.showwarning(
                "Thiếu số ảnh",
                "Nhập số ảnh cần chạy lại vào ô 'Bắt đầu từ ảnh' trước."
            )
            return

        if not getattr(sys, "frozen", False) and not SCRIPT_FILE.exists():
            messagebox.showerror("Lỗi", f"Không thấy file:\n{SCRIPT_FILE}")
            return

        self.save_settings()

        env = os.environ.copy()
        env["IMAGE_FOLDER"] = self.image_var.get()
        env["DOWNLOAD_FOLDER"] = self.output_var.get()
        env["PROFILE_DIR"] = self.profile_var.get()
        env["BATCH_SIZE"] = self.batch_var.get()
        env["START_FROM"] = self.start_from_var.get()
        env["RUN_MODE"] = mode
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        browser_path = APP_DIR / "ms-playwright"
        if getattr(sys, "frozen", False) or browser_path.exists():
            env["PLAYWRIGHT_BROWSERS_PATH"] = str(browser_path)

        self.current_done = 0
        self.current_total = 0
        self.progress_var.set(0)
        self.progress_label.set("Tiến trình: 0%")

        self.log(f"\n=== BẮT ĐẦU CHẠY: {mode.upper()} ===\n")
        self.status_var.set("Đang chạy...")
        self.start_btn.config(state="disabled")
        self.retry_btn.config(state="disabled")
        self.force_btn.config(state="disabled")
        self.continue_btn.config(state="disabled")

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        start_new_session = os.name != "nt"

        if getattr(sys, "frozen", False):
            command = [sys.executable, "--worker"]
        else:
            command = [sys.executable, "-u", str(SCRIPT_FILE)]

        popen_kwargs = {
            "cwd": str(APP_DIR),
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "stdin": subprocess.PIPE,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "env": env,
            "bufsize": 1,
            "creationflags": creationflags,
        }
        if start_new_session:
            popen_kwargs["start_new_session"] = True

        self.proc = subprocess.Popen(command, **popen_kwargs)

        threading.Thread(target=self.read_process_output, daemon=True).start()

    def read_process_output(self):
        try:
            for line in self.proc.stdout:
                self.log_queue.put(line)
        except Exception as e:
            self.log_queue.put(f"\n[LỖI ĐỌC LOG] {e}\n")
        finally:
            code = self.proc.wait()
            self.log_queue.put(f"\n=== KẾT THÚC, EXIT CODE: {code} ===\n")
            self.log_queue.put("__PROCESS_DONE__")

    def poll_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()

                if msg == "__PROCESS_DONE__":
                    self.status_var.set("Đã dừng / hoàn tất")
                    self.start_btn.config(state="normal")
                    self.retry_btn.config(state="normal")
                    self.force_btn.config(state="normal")
                    self.continue_btn.config(state="disabled")
                else:
                    self.log(msg)

        except queue.Empty:
            pass

        self.root.after(200, self.poll_log_queue)

    def log(self, text):
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.update_progress_from_log(text)
        self.update_manual_button_from_log(text)

    def update_manual_button_from_log(self, text):
        if "MANUAL_ACTION_REQUIRED" in text:
            self.status_var.set("Đang chờ bạn can thiệp trong trình duyệt...")
            self.continue_btn.config(state="normal")

    def update_progress_from_log(self, text):
        if "📌 Batch lần này:" in text:
            try:
                self.current_total = int(text.split(":")[-1].strip().split()[0])
                self.current_done = 0
                self.progress_var.set(0)
                self.progress_label.set(f"Tiến trình: 0/{self.current_total} ảnh")
            except Exception:
                pass

        if "✓ DONE" in text or "✗ Lỗi:" in text:
            self.current_done += 1
            total = max(self.current_total, 1)
            percent = self.current_done / total * 100
            self.progress_var.set(percent)
            self.progress_label.set(f"Tiến trình: {self.current_done}/{total} ảnh ({percent:.0f}%)")

    def send_continue(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.write("\n")
                self.proc.stdin.flush()
                self.continue_btn.config(state="disabled")
                self.status_var.set("Đã gửi lệnh tiếp tục...")
                self.log("\n=== ĐÃ GỬI LỆNH TIẾP TỤC ===\n")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không gửi được lệnh tiếp tục:\n{e}")

    def stop(self):
        if self.proc and self.proc.poll() is None:
            pid = self.proc.pid

            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                try:
                    os.killpg(pid, signal.SIGTERM)
                    self.proc.wait(timeout=8)
                except Exception:
                    try:
                        os.killpg(pid, signal.SIGKILL)
                    except Exception:
                        self.proc.kill()

            self.status_var.set("Đã dừng")
            self.log("\n=== ĐÃ DỪNG VÀ KILL SẠCH PROCESS CON ===\n")
        else:
            self.status_var.set("Không có tiến trình đang chạy")

    def open_output(self):
        folder = self.output_var.get()
        os.makedirs(folder, exist_ok=True)
        if os.name == "nt":
            os.startfile(folder)
        elif is_macos():
            subprocess.run(["open", folder], check=False)
        else:
            subprocess.run(["xdg-open", folder], check=False)

    def export_failed(self):
        progress_file = Path(self.output_var.get()) / "progress.csv"
        failed_file = Path(self.output_var.get()) / "failed_list.csv"

        if not progress_file.exists():
            messagebox.showerror("Lỗi", f"Không thấy file:\n{progress_file}")
            return

        rows = []

        with open(progress_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get("status") or "").lower() in ["fail", "failed", "manual", "error"]:
                    rows.append(row)

        if not rows:
            messagebox.showinfo("OK", "Không có ảnh lỗi.")
            return

        with open(failed_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["index", "file", "output", "status", "time", "note"])
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    "index": row.get("index", ""),
                    "file": row.get("file", ""),
                    "output": row.get("output", ""),
                    "status": row.get("status", ""),
                    "time": row.get("time", ""),
                    "note": row.get("note", "")
                })

        self.log(f"\n=== Đã xuất lỗi: {failed_file} ===\n")
        messagebox.showinfo("OK", f"Đã xuất {len(rows)} dòng lỗi.")

    def copy_failed_retry(self):
        image_folder = Path(self.image_var.get())
        output_folder = Path(self.output_var.get())
        progress_file = output_folder / "progress.csv"
        retry_folder = output_folder / "failed_retry"

        if not progress_file.exists():
            messagebox.showerror("Lỗi", f"Không thấy file:\n{progress_file}")
            return

        retry_folder.mkdir(parents=True, exist_ok=True)

        latest = {}

        with open(progress_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                file_name = row.get("file", "")
                if file_name:
                    latest[file_name] = row

        failed_files = [
            name for name, row in latest.items()
            if (row.get("status") or "").lower() in ["fail", "failed", "manual", "error"]
        ]

        copied = 0
        missing = []

        for name in failed_files:
            src = image_folder / name
            dst = retry_folder / name

            if src.exists():
                shutil.copy2(src, dst)
                copied += 1
            else:
                missing.append(name)

        self.log(f"\n=== Copy lỗi retry ===\nĐã copy: {copied}\nThư mục: {retry_folder}\n")

        if missing:
            missing_file = retry_folder / "missing_files.txt"
            with open(missing_file, "w", encoding="utf-8") as f:
                for name in missing:
                    f.write(name + "\n")
            self.log(f"Không tìm thấy: {len(missing)} file\n")

        messagebox.showinfo("OK", f"Đã copy {copied} ảnh lỗi sang:\n{retry_folder}")

    def clear_log(self):
        self.log_text.delete("1.0", "end")


if __name__ == "__main__":
    enable_windows_dpi_awareness()
    if "--worker" in sys.argv:
        run_packaged_worker()
        raise SystemExit(0)

    root = tk.Tk()
    app = ChatGPTBatchApp(root)
    root.mainloop()
