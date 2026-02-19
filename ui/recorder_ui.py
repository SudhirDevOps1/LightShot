from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QPoint, QTimer

class RecorderUI(QWidget):
    def __init__(self, on_stop_callback):
        super().__init__()
        self.on_stop_callback = on_stop_callback
        self.seconds = 0
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint | 
                           Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QHBoxLayout()
        self.setStyleSheet("""
            QWidget {
                background-color: #d32f2f;
                border-radius: 5px;
                color: white;
                padding: 5px;
            }
            QPushButton {
                background-color: #b71c1c;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        
        self.lbl_timer = QLabel("00:00")
        btn_stop = QPushButton("Stop Recording")
        btn_stop.clicked.connect(self.on_stop_callback)
        
        layout.addWidget(self.lbl_timer)
        layout.addWidget(btn_stop)
        self.setLayout(layout)

    def update_timer(self):
        self.seconds += 1
        m, s = divmod(self.seconds, 60)
        self.lbl_timer.setText(f"{m:02d}:{s:02d}")
