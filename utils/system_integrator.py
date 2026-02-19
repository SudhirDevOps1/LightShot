import sys
from pynput import keyboard
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction

class SystemIntegrator:
    def __init__(self, app, on_trigger_callback):
        self.app = app
        self.on_trigger_callback = on_trigger_callback
        self.listener = None

    def setup_global_shortcut(self):
        """Sets up the Ctrl+Shift+S global shortcut."""
        def on_activate():
            print("Global shortcut triggered!")
            self.on_trigger_callback()

        # Define the shortcut: Ctrl+Shift+S
        # Using a more robust combination for pynput
        combination = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('S')}
        current_keys = set()

        def on_press(key):
            if key in combination:
                current_keys.add(key)
                if all(k in current_keys for k in combination):
                    on_activate()

        def on_release(key):
            if key in current_keys:
                current_keys.remove(key)

        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.start()

    def setup_tray_icon(self, window):
        """Sets up the system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon(window)
        # Fallback icon if none provided
        self.tray_icon.setIcon(QIcon.fromTheme("camera-photo")) 
        
        menu = QMenu()
        
        capture_action = QAction("Capture Region", menu)
        capture_action.triggered.connect(self.on_trigger_callback)
        menu.addAction(capture_action)
        
        full_action = QAction("Capture Full Screen", menu)
        # connect to full screen logic
        menu.addAction(full_action)
        
        menu.addSeparator()
        
        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.app.quit)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def stop(self):
        if self.listener:
            self.listener.stop()
