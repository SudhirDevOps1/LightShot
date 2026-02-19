from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QFileDialog
from PyQt6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, file_manager):
        super().__init__()
        self.file_manager = file_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
        
        layout = QVBoxLayout()
        
        # Save Directory
        dir_layout = QHBoxLayout()
        self.edit_dir = QLineEdit(self.file_manager.config["save_dir"])
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.browse_dir)
        dir_layout.addWidget(QLabel("Save Directory:"))
        dir_layout.addWidget(self.edit_dir)
        dir_layout.addWidget(btn_browse)
        
        # Format
        fmt_layout = QHBoxLayout()
        self.combo_format = QComboBox()
        self.combo_format.addItems(["png", "jpeg"])
        self.combo_format.setCurrentText(self.file_manager.config["format"])
        fmt_layout.addWidget(QLabel("Image Format:"))
        fmt_layout.addWidget(self.combo_format)
        
        # Watermark
        self.check_watermark = QCheckBox("Enable Watermark")
        self.check_watermark.setChecked(self.file_manager.config.get("enable_watermark", False))
        
        # Save Button
        btn_save = QPushButton("Save Settings")
        btn_save.setStyleSheet("background-color: #0078d7; font-weight: bold; margin-top: 20px;")
        btn_save.clicked.connect(self.save_settings)
        
        layout.addLayout(dir_layout)
        layout.addLayout(fmt_layout)
        layout.addWidget(self.check_watermark)
        layout.addStretch()
        layout.addWidget(btn_save)
        
        self.setLayout(layout)

    def browse_dir(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Select Directory", self.edit_dir.text())
        if new_dir:
            self.edit_dir.setText(new_dir)

    def save_settings(self):
        new_config = {
            "save_dir": self.edit_dir.text(),
            "format": self.combo_format.currentText(),
            "enable_watermark": self.check_watermark.isChecked()
        }
        self.file_manager.save_config(new_config)
        self.accept()
