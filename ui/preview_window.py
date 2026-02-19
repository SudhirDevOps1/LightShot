from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QAction
import io
from PIL import Image

class PreviewWindow(QWidget):
    def __init__(self, pil_image, file_manager, image_processor):
        super().__init__()
        self.pil_image = pil_image
        self.file_manager = file_manager
        self.image_processor = image_processor
        self.init_ui()
        
        # Annotation state
        self.tool = "none" # none, blur, rect, arrow, text
        self.begin = QPoint()
        self.end = QPoint()
        self.is_drawing = False

    def init_ui(self):
        self.setWindowTitle("Screenshot Preview")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        
        main_layout = QVBoxLayout()
        
        # Tools layout
        tools_layout = QHBoxLayout()
        
        self.btn_blur = QPushButton("Blur")
        self.btn_blur.clicked.connect(lambda: self.set_tool("blur"))
        
        self.btn_pen = QPushButton("Pen")
        self.btn_pen.clicked.connect(lambda: self.set_tool("pen"))

        self.btn_rect = QPushButton("Rect")
        self.btn_rect.clicked.connect(lambda: self.set_tool("rect"))

        self.btn_arrow = QPushButton("Arrow")
        self.btn_arrow.clicked.connect(lambda: self.set_tool("arrow"))

        self.btn_text = QPushButton("Text")
        self.btn_text.clicked.connect(lambda: self.set_tool("text"))
        
        self.btn_save = QPushButton("Save")
        self.btn_save.setStyleSheet("background-color: #0078d7; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_screenshot)
        
        self.btn_copy = QPushButton("Copy")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)

        tools_layout.addWidget(self.btn_blur)
        tools_layout.addWidget(self.btn_pen)
        tools_layout.addWidget(self.btn_rect)
        tools_layout.addWidget(self.btn_arrow)
        tools_layout.addWidget(self.btn_text)
        tools_layout.addStretch()
        tools_layout.addWidget(self.btn_copy)
        tools_layout.addWidget(self.btn_save)
        
        # Image display area
        self.image_label = QLabel()
        self.update_preview()
        
        main_layout.addLayout(tools_layout)
        main_layout.addWidget(self.image_label)
        
        self.setLayout(main_layout)

    def set_tool(self, tool):
        self.tool = tool
        self.points = []
        self.setCursor(Qt.CursorShape.CrossCursor if tool != "none" else Qt.CursorShape.ArrowCursor)

    def update_preview(self):
        # Convert PIL to QPixmap
        byte_array = io.BytesIO()
        self.pil_image.save(byte_array, format="PNG")
        q_image = QImage.fromData(byte_array.getvalue())
        self.image_label.setPixmap(QPixmap.fromImage(q_image))

    def mousePressEvent(self, event):
        if self.tool != "none" and event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint() - self.image_label.pos()
            self.begin = pos
            self.points = [ (pos.x(), pos.y()) ]
            self.is_drawing = True

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            pos = event.position().toPoint() - self.image_label.pos()
            self.end = pos
            if self.tool == "pen":
                self.points.append( (pos.x(), pos.y()) )
                # For pen, we apply incrementally to preview or just wait
                # To make it feel better, we'd need a multi-layer approach. 
                # For now, let's keep it simple.
            self.update()

    def mouseReleaseEvent(self, event):
        if self.is_drawing:
            pos = event.position().toPoint() - self.image_label.pos()
            self.end = pos
            self.is_drawing = False
            self.apply_tool()

    def apply_tool(self):
        rect = QRect(self.begin, self.end).normalized()
        box = (rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
        start = (self.begin.x(), self.begin.y())
        end = (self.end.x(), self.end.y())
        
        if self.tool == "blur":
            self.pil_image = self.image_processor.apply_blur(self.pil_image, box)
        elif self.tool == "rect":
            self.pil_image = self.image_processor.draw_annotation(self.pil_image, "rect", start, end)
        elif self.tool == "arrow":
            self.pil_image = self.image_processor.draw_annotation(self.pil_image, "arrow", start, end)
        elif self.tool == "pen":
            self.pil_image = self.image_processor.draw_annotation(self.pil_image, "pen", None, None, points=self.points)
        elif self.tool == "text":
            from PyQt6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self, "Text Annotation", "Enter text:")
            if ok and text:
                self.pil_image = self.image_processor.draw_annotation(self.pil_image, "text", start, None, text=text)
        
        self.update_preview()
        self.tool = "none"
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def save_screenshot(self):
        path = self.file_manager.save_screenshot(self.pil_image)
        QMessageBox.information(self, "Saved", f"Screenshot saved to:\n{path}")
        self.close()

    def copy_to_clipboard(self):
        from PyQt6.QtWidgets import QApplication
        byte_array = io.BytesIO()
        self.pil_image.save(byte_array, format="PNG")
        q_image = QImage.fromData(byte_array.getvalue())
        QApplication.clipboard().setImage(q_image)
        # toast notification would be better here
        print("Copied to clipboard")
