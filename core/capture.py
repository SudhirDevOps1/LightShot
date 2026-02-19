import mss
import mss.tools
from PIL import Image
import os

class CaptureManager:
    def __init__(self):
        self.sct = mss.mss()

    def get_monitors(self):
        """Returns a list of all monitors."""
        return self.sct.monitors

    def capture_full_screen(self, monitor_index=0):
        """
        Captures the full screen of a specific monitor or all monitors.
        monitor_index: 0 for all monitors combined, 1+ for specific monitor.
        """
        monitor = self.sct.monitors[monitor_index]
        sct_img = self.sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img

    def capture_region(self, x, y, width, height):
        """Captures a specific screen region."""
        region = {"top": y, "left": x, "width": width, "height": height}
        sct_img = self.sct.grab(region)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img

    def capture_active_window(self):
        """
        Captures the currently active window.
        Note: On Windows, this requires pywin32 to get window coordinates.
        """
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x2, y2 = rect
            w = x2 - x
            h = y2 - y
            return self.capture_region(x, y, w, h)
        except ImportError:
            # Fallback or log error
            return self.capture_full_screen(1)

    def close(self):
        self.sct.close()
