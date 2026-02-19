from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QIcon

class FloatingToolbar(QWidget):
    capture_clicked = pyqtSignal()
    full_screen_clicked = pyqtSignal()
    record_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        self._drag_pos = QPoint()

    def init_ui(self):
        # Set window flags for frameless, always-on-top, and tool window style
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint | 
                           Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Modern dark styling
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-radius: 10px;
                border: 1px solid #3d3d3d;
            }
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                border: none;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-radius: 5px;
            }
        """)

        btn_capture = QPushButton("📷")
        btn_capture.setToolTip("Capture Region")
        btn_capture.clicked.connect(self.capture_clicked.emit)
        
        btn_full = QPushButton("🖥️")
        btn_full.setToolTip("Capture Full Screen")
        btn_full.clicked.connect(self.full_screen_clicked.emit)

        btn_record = QPushButton("⏺️")
        btn_record.setToolTip("Record Screen")
        btn_record.clicked.connect(self.record_clicked.emit)

        btn_settings = QPushButton("⚙️")
        btn_settings.setToolTip("Settings")
        btn_settings.clicked.connect(self.settings_clicked.emit)

        layout.addWidget(btn_capture)
        layout.addWidget(btn_full)
        layout.addWidget(btn_record)
        layout.addWidget(btn_settings)
        
        self.setLayout(layout)
        self.setFixedSize(150, 45)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
