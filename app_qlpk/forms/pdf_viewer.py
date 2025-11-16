from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import fitz  # PyMuPDF
import os

class PDFViewer(QWidget):
    def __init__(self, file_path):
        super().__init__()
        self.setWindowTitle(f"Xem phiếu - {os.path.basename(file_path)}")
        self.resize(900, 700)

        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        container = QWidget()
        vbox = QVBoxLayout(container)

        # ✅ Mở file PDF và render từng trang thành ảnh
        doc = fitz.open(file_path)
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # độ phân giải cao
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

            label = QLabel()
            label.setPixmap(QPixmap.fromImage(img))
            label.setAlignment(Qt.AlignCenter)
            vbox.addWidget(label)

        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
