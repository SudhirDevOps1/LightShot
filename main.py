import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import sys
import os
import io
from PIL import Image, ImageTk, ImageGrab
import threading

import mss
from core.capture import CaptureManager
from core.manager import FileManager
from core.recorder import ScreenRecorder
from utils.image_processor import ImageProcessor

class ScreenshotApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LightShot")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception: pass

        self.capture_manager = CaptureManager()
        self.file_manager = FileManager()
        self.image_processor = ImageProcessor()
        self.recorder = ScreenRecorder(self.file_manager)

        self.setup_ui()
        self.setup_integrator()

        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.on_drag)

    def setup_ui(self):
        self.root.configure(bg="#121212")
        # Branding header
        header = tk.Frame(self.root, bg="#1e1e1e", pady=2)
        header.pack(fill=tk.X)
        tk.Label(header, text="  📸 LightShot", fg="#0078d7", bg="#1e1e1e", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        self.status_label = tk.Label(header, text="", fg="#aaa", bg="#1e1e1e", font=("Arial", 7, "italic"))
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        container = tk.Frame(self.root, bg="#121212", padx=6, pady=6)
        container.pack()

        # Vertical buttons with Icons and Labels
        self.create_btn(container, "📷", "Region", self.start_region_capture).pack(side=tk.LEFT, padx=3)
        self.create_btn(container, "🖥️", "Full", self.capture_full_screen).pack(side=tk.LEFT, padx=3)
        self.create_btn(container, "🚀", "Auto", self.capture_auto_save).pack(side=tk.LEFT, padx=3)
        self.btn_rec = self.create_btn(container, "⏺️", "Rec", self.toggle_recording)
        self.btn_rec.pack(side=tk.LEFT, padx=3)
        self.create_btn(container, "⚙️", "Sett", self.open_settings).pack(side=tk.LEFT, padx=3)
        
        close_btn = tk.Button(container, text="✕", command=self.root.destroy, bg="#333", fg="white", 
                             relief="flat", font=("Arial", 10), padx=8, pady=4, activebackground="#e81123", activeforeground="white")
        close_btn.pack(side=tk.LEFT, padx=3)
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg="#e81123"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg="#333"))

    def create_btn(self, parent, icon, label_text, cmd, bg="#333"):
        btn = tk.Button(parent, text=f"{icon}\n{label_text}", command=cmd, bg=bg, fg="white", relief="flat", 
                       font=("Segoe UI Emoji", 9), padx=10, pady=5, activebackground="#444", justify=tk.CENTER)
        btn.bind("<Enter>", lambda e: btn.config(bg="#444"))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    def setup_integrator(self):
        try:
            from pynput import keyboard
            def on_activate(): self.root.after(0, self.start_region_capture)
            self.hotkey = keyboard.GlobalHotKeys({'<ctrl>+<shift>+s': on_activate})
            self.hotkey.start()
        except: pass

    def start_drag(self, event):
        self.x, self.y = event.x, event.y

    def on_drag(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    def start_region_capture(self):
        self.root.withdraw()
        SelectionOverlay(self.on_region_selected)

    def on_region_selected(self, x, y, w, h):
        self.root.deiconify()
        if w > 5 and h > 5:
            img = self.capture_manager.capture_region(x, y, w, h)
            path = self.file_manager.save_screenshot(img)
            self.show_preview(img, path)

    def capture_full_screen(self):
        self.root.withdraw()
        self.root.after(150, self._do_full_capture)

    def _do_full_capture(self):
        img = self.capture_manager.capture_full_screen(1)
        path = self.file_manager.save_screenshot(img)
        self.root.deiconify()
        self.show_preview(img, path)

    def capture_auto_save(self):
        self.root.withdraw()
        self.root.after(150, self._do_auto_capture)

    def _do_auto_capture(self):
        img = self.capture_manager.capture_full_screen(1)
        path = self.file_manager.save_screenshot(img)
        self.root.deiconify()
        self.status_label.config(text="✅ Saved!", fg="#4CAF50")
        self.root.after(2000, lambda: self.status_label.config(text="", fg="#aaa"))

    def toggle_recording(self):
        if self.recorder.is_saving: return
        if not self.recorder.is_recording:
            self.root.withdraw()
            self.recorder.start_recording(1)
            self.btn_rec.config(text="⏹️", bg="#d83b01")
            self.show_recording_ui()
        else: self.stop_recording()

    def show_recording_ui(self):
        self.rec_ui = tk.Toplevel()
        self.rec_ui.overrideredirect(True)
        self.rec_ui.attributes("-topmost", True)
        self.rec_ui.geometry("140x50+20+20")
        self.rec_ui.configure(bg="#222")
        tk.Button(self.rec_ui, text="Stop Recording", bg="#d83b01", fg="white", font=("Arial", 10, "bold"), 
                  relief="flat", command=self.stop_recording).pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def stop_recording(self):
        if hasattr(self, 'rec_ui'): 
            try: self.rec_ui.destroy()
            except: pass
        self.btn_rec.config(text="⏺️", bg="#333")
        self.root.deiconify()
        
        # Show subtle background status
        self.status_label.config(text="⏳ Processing...")
        
        def on_save_done(path):
            self.root.after(0, lambda: self.finalize_save(path))
        self.recorder.stop_recording(callback=on_save_done)

    def finalize_save(self, path):
        self.status_label.config(text="") # Clear background status
        try: os.startfile(os.path.dirname(path))
        except: pass

    def show_preview(self, img, path=None):
        PreviewWindow(img, self.file_manager, self.image_processor, saved_path=path)

    def open_settings(self):
        SettingsWindow(self.file_manager)

    def run(self):
        self.root.mainloop()

class SelectionOverlay:
    def __init__(self, callback):
        self.callback = callback
        self.win = tk.Toplevel()
        with mss.mss() as sct:
            vscr = sct.monitors[0]
            self.win.geometry(f"{vscr['width']}x{vscr['height']}+{vscr['left']}+{vscr['top']}")
        
        self.win.attributes("-alpha", 0.35, "-topmost", True)
        self.win.overrideredirect(True)
        self.win.configure(bg="#000")
        
        self.canvas = tk.Canvas(self.win, highlightthickness=0, bg="#000", cursor="tcross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.start_x = self.start_y = self.rect = None
        self.v_line = self.h_line = None
        
        self.win.bind("<ButtonPress-1>", self.on_press)
        self.win.bind("<B1-Motion>", self.on_drag)
        self.win.bind("<ButtonRelease-1>", self.on_release)
        self.win.bind("<Motion>", self.draw_crosshair)
        self.win.bind("<Escape>", lambda e: self.win.destroy())

    def draw_crosshair(self, event):
        if self.v_line: self.canvas.delete(self.v_line)
        if self.h_line: self.canvas.delete(self.h_line)
        # Subtle guide lines
        self.v_line = self.canvas.create_line(event.x, 0, event.x, self.win.winfo_height(), fill="#fff", dash=(4, 4))
        self.h_line = self.canvas.create_line(0, event.y, self.win.winfo_width(), event.y, fill="#fff", dash=(4, 4))

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline="#0078d7", width=2)

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
        self.draw_crosshair(event)

    def on_release(self, event):
        coords = self.canvas.coords(self.rect)
        self.win.destroy()
        self.callback(int(min(coords[0], coords[2])), int(min(coords[1], coords[3])), int(abs(coords[2]-coords[0])), int(abs(coords[3]-coords[1])))

class PreviewWindow:
    def __init__(self, pil_img, file_manager, processor, saved_path=None):
        self.pil_img, self.file_manager, self.processor, self.saved_path = pil_img, file_manager, processor, saved_path
        self.tool, self.temp_shape = "none", None
        self.scale = 1.0 # Current display scale
        
        self.win = tk.Toplevel()
        self.win.title("LightShot Editor")
        self.win.attributes("-topmost", True)
        self.win.configure(bg="#1a1a1a")
        
        controls = tk.Frame(self.win, bg="#222", pady=4)
        controls.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(controls, text="💾 Save Edits", command=self.save, bg="#0078d7", fg="white", relief="flat", padx=15, pady=4).pack(side=tk.LEFT, padx=10)
        
        tools = [("📋 Copy", self.copy_to_clipboard), ("🌫️ Blur", lambda: self.set_tool("blur")), 
                 ("✏️ Pen", lambda: self.set_tool("pen")), ("⬜ Rect", lambda: self.set_tool("rect")), 
                 ("↗️ Arrow", lambda: self.set_tool("arrow")), ("T Text", lambda: self.set_tool("text")), 
                 ("© Mark", self.apply_watermark)]
        
        for text, cmd in tools:
            b = tk.Button(controls, text=text, command=cmd, bg="#333", fg="#ccc", relief="flat", padx=8, pady=4, activebackground="#444")
            b.pack(side=tk.LEFT, padx=1)
            b.bind("<Enter>", lambda e, bt=b: bt.config(bg="#444", fg="white"))
            b.bind("<Leave>", lambda e, bt=b: bt.config(bg="#333", fg="#ccc"))

        self.canvas = tk.Canvas(self.win, bg="#000", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.update_canvas()
        
        self.canvas.bind("<ButtonPress-1>", self.start_action)
        self.canvas.bind("<B1-Motion>", self.on_action)
        self.canvas.bind("<ButtonRelease-1>", self.end_action)

    def set_tool(self, tool): self.tool = tool; self.canvas.config(cursor="tcross")

    def apply_watermark(self):
        txt = simpledialog.askstring("Watermark", "Text:", parent=self.win)
        if txt: self.pil_img = self.processor.add_watermark(self.pil_img, txt); self.update_canvas()

    def copy_to_clipboard(self):
        import win32clipboard
        output = io.BytesIO()
        self.pil_img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        messagebox.showinfo("📋", "Copied to clipboard!")

    def update_canvas(self):
        limit_w, limit_h = self.win.winfo_screenwidth()-80, self.win.winfo_screenheight()-120
        disp = self.pil_img.copy()
        self.scale = 1.0
        if disp.width > limit_w or disp.height > limit_h:
            # Calculate scale
            self.scale = min(limit_w / disp.width, limit_h / disp.height)
            new_size = (int(disp.width * self.scale), int(disp.height * self.scale))
            disp = disp.resize(new_size, Image.Resampling.LANCZOS)
            
        self.tk_img = ImageTk.PhotoImage(disp)
        self.canvas.config(width=disp.width, height=disp.height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

    def start_action(self, event):
        if self.tool == "none": return
        self.start_x, self.start_y, self.points = event.x, event.y, [(event.x, event.y)]

    def on_action(self, event):
        if self.tool == "none": return
        if self.tool == "pen":
            self.points.append((event.x, event.y))
            self.canvas.create_line(self.points[-2], self.points[-1], fill="#ff0000", width=2)
        else:
            if self.temp_shape: self.canvas.delete(self.temp_shape)
            if self.tool in ["rect", "blur"]: self.temp_shape = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="#ff0000", width=2)
            elif self.tool == "arrow": self.temp_shape = self.canvas.create_line(self.start_x, self.start_y, event.x, event.y, arrow=tk.LAST, fill="#ff0000", width=2)

    def end_action(self, event):
        if self.tool == "none": return
        # Scale back to original coordinates
        inv = 1.0 / self.scale
        x1, y1 = int(self.start_x * inv), int(self.start_y * inv)
        x2, y2 = int(event.x * inv), int(event.y * inv)
        
        l, r, t, b = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
        try:
            if self.tool == "blur" and r > l: self.pil_img = self.processor.apply_blur(self.pil_img, (l, t, r, b))
            elif self.tool == "pen":
                scaled_points = [(int(px * inv), int(py * inv)) for px, py in self.points]
                self.pil_img = self.processor.draw_annotation(self.pil_img, "pen", None, None, points=scaled_points)
            elif self.tool == "rect": self.pil_img = self.processor.draw_annotation(self.pil_img, "rect", (l, t), (r, b))
            elif self.tool == "arrow": self.pil_img = self.processor.draw_annotation(self.pil_img, "arrow", (x1, y1), (x2, y2))
            elif self.tool == "text":
                txt = simpledialog.askstring("T", "Text:", parent=self.win)
                if txt: self.pil_img = self.processor.draw_annotation(self.pil_img, "text", (x1, y1), None, text=txt)
        except Exception as e: print(e)
        self.update_canvas()

    def save(self):
        p = self.file_manager.save_screenshot(self.pil_img, path=self.saved_path)
        messagebox.showinfo("✅", f"Updated: {os.path.basename(p)}")
        self.win.destroy()

class SettingsWindow:
    def __init__(self, file_manager):
        self.fm = file_manager
        self.win = tk.Toplevel()
        self.win.title("Settings")
        self.win.geometry("400x240")
        self.win.attributes("-topmost", True)
        self.win.configure(bg="#1a1a1a")
        
        # Save Dir
        tk.Label(self.win, text="Save Screenshots to:", fg="#888", bg="#1a1a1a", font=("Arial", 9)).pack(pady=(15, 5))
        f = tk.Frame(self.win, bg="#1a1a1a"); f.pack(fill=tk.X, padx=30)
        self.ent = tk.Entry(f, bg="#252525", fg="white", relief="flat", insertbackground="white")
        self.ent.insert(0, self.fm.config["save_dir"])
        self.ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        tk.Button(f, text="📂", command=self.browse, bg="#333", fg="white", relief="flat").pack(side=tk.LEFT, padx=5)
        
        # Record Format
        tk.Label(self.win, text="Recording Format:", fg="#888", bg="#1a1a1a", font=("Arial", 9)).pack(pady=(15, 5))
        self.fmt_var = tk.StringVar(value=self.fm.config.get("rec_format", "gif"))
        fmt_frame = tk.Frame(self.win, bg="#1a1a1a")
        fmt_frame.pack()
        tk.Radiobutton(fmt_frame, text="GIF (Lightweight)", variable=self.fmt_var, value="gif", bg="#1a1a1a", fg="white", selectcolor="#333", activebackground="#1a1a1a").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(fmt_frame, text="MP4 (HQ - FFmpeg)", variable=self.fmt_var, value="mp4", bg="#1a1a1a", fg="white", selectcolor="#333", activebackground="#1a1a1a").pack(side=tk.LEFT, padx=10)

        tk.Button(self.win, text="Apply & Save Settings", bg="#0078d7", fg="white", relief="flat", pady=8, font=("Arial", 10, "bold"), command=self.save_cfg).pack(pady=20)

    def browse(self):
        d = filedialog.askdirectory()
        if d: self.ent.delete(0, tk.END); self.ent.insert(0, os.path.normpath(d))

    def save_cfg(self):
        new_dir = self.ent.get()
        if not os.path.exists(new_dir):
            try: os.makedirs(new_dir)
            except: messagebox.showerror("Error", "Invalid Directory"); return
        
        self.fm.save_config({
            "save_dir": new_dir,
            "rec_format": self.fmt_var.get()
        })
        messagebox.showinfo("Settings", "Settings saved successfully!")
        self.win.destroy()

if __name__ == "__main__":
    ScreenshotApp().run()
