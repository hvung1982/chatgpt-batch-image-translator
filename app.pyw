import os
import sys
import csv
import json
import queue
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SCRIPT_FILE = APP_DIR / "run_chatgpt_batch.py"
SETTINGS_FILE = APP_DIR / "app_settings.json"

DEFAULT_SETTINGS = {
    "image_folder": str(APP_DIR / "images"),
    "download_folder": str(APP_DIR / "images_vn"),
    "profile_dir": str(APP_DIR / "chatgpt_auto_profile"),
    "batch_size": "5",
    "start_from": ""
}


class ChatGPTBatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ChatGPT Batch Translator PRO")
        self.root.geometry("1080x780")
        self.root.minsize(980, 700)

        self.proc = None
        self.log_queue = queue.Queue()
        self.current_done = 0
        self.current_total = 0

        self.settings = self.load_settings()

        self.setup_style()
        self.build_ui()
        self.poll_log_queue()

    def setup_style(self):
        self.root.configure(bg="#f3f4f6")

        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure("TFrame", background="#f3f4f6")
        self.style.configure("Card.TFrame", background="#ffffff", relief="flat")

        self.style.configure(
            "Title.TLabel",
            background="#f3f4f6",
            foreground="#111827",
            font=("Segoe UI", 18, "bold")
        )

        self.style.configure(
            "Sub.TLabel",
            background="#f3f4f6",
            foreground="#6b7280",
            font=("Segoe UI", 10)
        )

        self.style.configure(
            "TLabel",
            background="#ffffff",
            foreground="#111827",
            font=("Segoe UI", 10)
        )

        self.style.configure("TEntry", font=("Segoe UI", 10), padding=6)

        self.style.configure(
            "Blue.TButton",
            background="#2563eb",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8)
        )

        self.style.map("Blue.TButton", background=[("active", "#1d4ed8"), ("disabled", "#93c5fd")])

        self.style.configure(
            "Purple.TButton",
            background="#7c3aed",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8)
        )

        self.style.map("Purple.TButton", background=[("active", "#6d28d9"), ("disabled", "#c4b5fd")])

        self.style.configure(
            "Green.TButton",
            background="#16a34a",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8)
        )

        self.style.map("Green.TButton", background=[("active", "#15803d"), ("disabled", "#86efac")])

        self.style.configure(
            "Red.TButton",
            background="#dc2626",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8)
        )

        self.style.map("Red.TButton", background=[("active", "#b91c1c")])

        self.style.configure(
            "Gray.TButton",
            background="#e5e7eb",
            foreground="#111827",
            font=("Segoe UI", 10),
            padding=(10, 8)
        )

        self.style.map("Gray.TButton", background=[("active", "#d1d5db")])

        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#e5e7eb",
            background="#2563eb",
            thickness=14
        )

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
            "start_from": self.start_from_var.get()
        }

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def build_ui(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 14))

        ttk.Label(
            header,
            text="ChatGPT Batch Translator PRO",
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            header,
            text="Tự động dịch ảnh, tạo ảnh tiếng Việt, tải kết quả và quản lý lỗi theo batch.",
            style="Sub.TLabel"
        ).pack(anchor="w", pady=(4, 0))

        config_card = ttk.Frame(outer, style="Card.TFrame", padding=14)
        config_card.pack(fill="x", pady=(0, 12))

        self.image_var = tk.StringVar(value=self.settings["image_folder"])
        self.output_var = tk.StringVar(value=self.settings["download_folder"])
        self.profile_var = tk.StringVar(value=self.settings["profile_dir"])
        self.batch_var = tk.StringVar(value=self.settings["batch_size"])
        self.start_from_var = tk.StringVar(value=self.settings.get("start_from", ""))

        self.add_folder_row(config_card, "Thư mục ảnh gốc", self.image_var, 0)
        self.add_folder_row(config_card, "Thư mục lưu ảnh VN", self.output_var, 1)
        self.add_folder_row(config_card, "Profile ChatGPT", self.profile_var, 2)

        ttk.Label(config_card, text="Số ảnh mỗi lần").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=8)
        ttk.Entry(config_card, textvariable=self.batch_var, width=12).grid(row=3, column=1, sticky="w", pady=8)

        ttk.Label(config_card, text="Bắt đầu từ ảnh").grid(row=4, column=0, sticky="w", padx=(0, 10), pady=8)
        ttk.Entry(config_card, textvariable=self.start_from_var, width=24).grid(row=4, column=1, sticky="w", pady=8)

        ttk.Label(
            config_card,
            text="Ví dụ: 66 hoặc 122 hoặc 66_122 hoặc 66_122.jpg",
            foreground="#6b7280"
        ).grid(row=4, column=1, sticky="w", padx=(180, 0), pady=8)

        config_card.columnconfigure(1, weight=1)

        action_card = ttk.Frame(outer, style="Card.TFrame", padding=14)
        action_card.pack(fill="x", pady=(0, 12))

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

        tools = ttk.Frame(action_card, style="Card.TFrame")
        tools.pack(side="right")

        ttk.Button(tools, text="Mở kết quả", command=self.open_output, style="Gray.TButton").pack(side="left", padx=4)
        ttk.Button(tools, text="Xuất lỗi", command=self.export_failed, style="Gray.TButton").pack(side="left", padx=4)
        ttk.Button(tools, text="Copy lỗi", command=self.copy_failed_retry, style="Gray.TButton").pack(side="left", padx=4)
        ttk.Button(tools, text="Lưu cấu hình", command=self.save_and_notify, style="Gray.TButton").pack(side="left", padx=4)
        ttk.Button(tools, text="Xóa log", command=self.clear_log, style="Gray.TButton").pack(side="left", padx=4)

        status_card = ttk.Frame(outer, style="Card.TFrame", padding=14)
        status_card.pack(fill="x", pady=(0, 12))

        self.status_var = tk.StringVar(value="Sẵn sàng")
        ttk.Label(status_card, textvariable=self.status_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")

        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(
            status_card,
            variable=self.progress_var,
            maximum=100,
            style="Horizontal.TProgressbar"
        ).pack(fill="x", pady=(10, 6))

        self.progress_label = tk.StringVar(value="Tiến trình: 0%")
        ttk.Label(status_card, textvariable=self.progress_label).pack(anchor="w")

        log_card = ttk.Frame(outer, style="Card.TFrame", padding=12)
        log_card.pack(fill="both", expand=True)

        ttk.Label(
            log_card,
            text="Nhật ký xử lý",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        self.log_text = ScrolledText(
            log_card,
            wrap="word",
            font=("Consolas", 10),
            bg="#0f172a",
            fg="#e5e7eb",
            insertbackground="white",
            relief="flat",
            padx=10,
            pady=10
        )
        self.log_text.pack(fill="both", expand=True)

    def add_folder_row(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=8)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", pady=8)
        ttk.Button(
            parent,
            text="Chọn",
            command=lambda: self.choose_folder(var),
            style="Gray.TButton"
        ).grid(row=row, column=2, padx=(10, 0), pady=8)

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

        if not SCRIPT_FILE.exists():
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

        self.current_done = 0
        self.current_total = 0
        self.progress_var.set(0)
        self.progress_label.set("Tiến trình: 0%")

        self.log(f"\n=== BẮT ĐẦU CHẠY: {mode.upper()} ===\n")
        self.status_var.set("Đang chạy...")
        self.start_btn.config(state="disabled")
        self.retry_btn.config(state="disabled")
        self.continue_btn.config(state="disabled")

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        self.proc = subprocess.Popen(
            [sys.executable, "-u", str(SCRIPT_FILE)],
            cwd=str(APP_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            bufsize=1,
            creationflags=creationflags
        )

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
                self.proc.terminate()

            self.status_var.set("Đã dừng")
            self.log("\n=== ĐÃ DỪNG VÀ KILL SẠCH PROCESS CON ===\n")
        else:
            self.status_var.set("Không có tiến trình đang chạy")

    def open_output(self):
        folder = self.output_var.get()
        os.makedirs(folder, exist_ok=True)
        os.startfile(folder)

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
    root = tk.Tk()
    app = ChatGPTBatchApp(root)
    root.mainloop()